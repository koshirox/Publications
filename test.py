from uuid import uuid4

from sqlalchemy import select

from database import SessionLocal
from models import Category, Post, User
from crud_categories import (
    create_category, delete_category, get_category, list_categories, rename_category,
)
from crud_comments import (
    change_comment, create_comment, delete_comment, get_comments,
)
from crud_posts import (
    category_feed, change_post, create_draft, delete_draft,
    delete_post_as_moderator, general_feed, get_post, hide_post, publish_post,
)
from crud_users import personal_feed, subscribe, unsubscribe
from crud_users import (
    change_email, create_user, delete_user, get_user,
    grant_moderator,
)
from crud_likes import (
    get_likes_count, get_user_liked_posts, has_liked, like_post, unlike_post,
)

def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return
    raise AssertionError(f"Ожидалась ошибка {error_type.__name__}")

# уникальный суффикс - чтобы email и названия не пересекались между запусками
tag = uuid4().hex[:8]

with SessionLocal() as session:
    # берём админа и категорию "Новости" (создано в fill_data.py)
    admin = session.scalar(select(User).where(User.role == "admin"))
    news = session.scalar(select(Category).where(Category.name == "Новости"))
    if admin is None or news is None:
        raise RuntimeError("Сначала запусти init_db.py, затем fill_data.py")

    # 1. Пользователи
    author = create_user(session, admin.id, f"author-{tag}@example.com")
    reader = create_user(session, admin.id, f"reader-{tag}@example.com")
    moderator = create_user(session, admin.id, f"moderator-{tag}@example.com", "moderator")
    temporary = create_user(session, admin.id, f"temp-{tag}@example.com")

    # смена email
    change_email(session, temporary.id, f"updated-{tag}@example.com")
    assert get_user(session, temporary.id).email.startswith("updated-")

    # повышение до модератора
    grant_moderator(session, admin.id, temporary.id)
    assert temporary.role == "moderator"

    # удаление (сначала сохраняем id, потом проверяем, что юзера нет)
    temporary_id = temporary.id
    delete_user(session, admin.id, temporary_id)
    assert get_user(session, temporary_id) is None

    # не-админ не может создавать пользователей
    expect_error(PermissionError, lambda: create_user(session, reader.id, f"bad-{tag}@example.com"))
    print("1. Пользователи: CRUD, права, смена роли, удаление - ОК")

    # 2. Категории
    category = create_category(session, admin.id, f"Учёба-{tag}")
    assert get_category(session, category.id) is not None
    assert category.id in [item.id for item in list_categories(session)]

    # модератор тоже может создавать/переименовывать/удалять
    mod_cat = create_category(session, moderator.id, f"Мод-{tag}")
    rename_category(session, moderator.id, mod_cat.id, f"Мод-переим-{tag}")
    assert get_category(session, mod_cat.id).name == f"Мод-переим-{tag}"
    delete_category(session, moderator.id, mod_cat.id)
    assert get_category(session, mod_cat.id) is None

    # обычный user не может
    expect_error(PermissionError, lambda: create_category(session, reader.id, f"Нет-{tag}"))
    print("2. Категории: админ и модератор могут, обычный user - нет - ОК")

    # 3. Черновик
    post = create_draft(session, author.id, category.id, "Черновик", "# v1")
    post_id = post.id

    # редактирование
    change_post(session, post_id, author.id, "Готовый", "# Заголовок\n\n**Текст**")
    assert get_post(session, post_id).body.startswith("# Заголовок")

    # черновик не виден в лентах
    assert post_id not in [p.id for p in general_feed(session)]
    assert post_id not in [p.id for p in category_feed(session, category.id)]

    # черновик нельзя комментировать
    expect_error(ValueError, lambda: create_comment(session, post_id, reader.id, "Рано"))
    # чужой пост нельзя менять
    expect_error(PermissionError, lambda: change_post(session, post_id, reader.id, "Чужой", "Текст"))
    # нельзя создать пост в несуществующей категории
    expect_error(ValueError, lambda: create_draft(session, author.id, -1, "Нет категории", "x"))

    # удаление своего черновика
    extra = create_draft(session, author.id, category.id, "Лишний", "Удалим")
    delete_draft(session, extra.id, author.id)
    assert get_post(session, extra.id) is None
    print("3. Черновик: создан, отредактирован, удалён; в ленте не виден - ОК")

    # 4. Подписка и публикация
    # повторная подписка не создаёт дубликат
    subscribe(session, reader.id, author.id)
    subscribe(session, reader.id, author.id)
    # на себя подписаться нельзя
    expect_error(ValueError, lambda: subscribe(session, reader.id, reader.id))

    # публикация
    publish_post(session, post_id, author.id)
    assert post.published_at is not None

    # после публикации пост виден во всех трёх лентах
    assert post_id in [p.id for p in general_feed(session)]
    assert post_id in [p.id for p in category_feed(session, category.id)]
    assert post_id in [p.id for p in personal_feed(session, reader.id)]

    # категорию с постами удалить нельзя
    expect_error(ValueError, lambda: delete_category(session, admin.id, category.id))
    print(f"4. Пост id={post_id} опубликован и есть во всех трёх лентах - ОК")

    # 5. Лайки
    # два раза подряд = один лайк
    like_post(session, reader.id, post_id)
    like_post(session, reader.id, post_id)
    assert get_likes_count(session, post_id) == 1
    assert has_liked(session, reader.id, post_id) is True
    assert has_liked(session, author.id, post_id) is False
    assert post_id in [p.id for p in get_user_liked_posts(session, reader.id)]

    # черновик лайкать нельзя
    draft_like = create_draft(session, author.id, category.id, "Черновик для лайка", "x")
    expect_error(ValueError, lambda: like_post(session, reader.id, draft_like.id))
    # от несуществующего юзера лайкать нельзя
    expect_error(ValueError, lambda: like_post(session, 999999, post_id))

    # два раза снять = 0 лайков, без ошибок
    unlike_post(session, reader.id, post_id)
    unlike_post(session, reader.id, post_id)
    assert get_likes_count(session, post_id) == 0
    print("5. Лайки: поставить, повторно, снять - идемпотентно - ОК")

    # 6. Комментарии
    comment = create_comment(session, post_id, reader.id, "Первый вариант")
    # автор правит свой комментарий
    change_comment(session, comment.id, reader.id, "Исправленный вариант")
    assert [(c.id, c.body) for c in get_comments(session, post_id)] == [
        (comment.id, "Исправленный вариант")
    ]
    # чужой комментарий менять нельзя
    expect_error(PermissionError, lambda: change_comment(session, comment.id, author.id, "Чужая правка"))
    # модератор удаляет чужой
    delete_comment(session, comment.id, moderator.id)
    # автор удаляет свой
    own = create_comment(session, post_id, reader.id, "Удалю сам")
    delete_comment(session, own.id, reader.id)
    assert get_comments(session, post_id) == []
    print("6. Комментарии: создание, правка, удаление автором и модератором - ОК")

    # 7. Модерация
    # удаление чужого поста вместе с комментариями
    removable = create_draft(session, author.id, category.id, "На удаление", "x")
    publish_post(session, removable.id, author.id)
    create_comment(session, removable.id, reader.id, "Исчезнет вместе с постом")
    # не-модератор удалять чужое не может
    expect_error(PermissionError, lambda: delete_post_as_moderator(session, removable.id, reader.id))
    delete_post_as_moderator(session, removable.id, moderator.id)
    assert get_post(session, removable.id) is None
    assert get_comments(session, removable.id) == []

    # скрытие чужого опубликованного поста
    hide_post(session, post_id, moderator.id)
    assert get_post(session, post_id).status == "hidden"
    assert post_id not in [p.id for p in general_feed(session)]
    print("7. Модератор удалил чужой пост с комментами и скрыл другой - ОК")

    # 8. Отписка
    visible = create_draft(session, author.id, news.id, "Проверка отписки", "# news")
    publish_post(session, visible.id, author.id)
    # пока подписан — пост в персональной ленте
    assert visible.id in [p.id for p in personal_feed(session, reader.id)]

    # после отписки — уходит из персональной, но остаётся в общей
    unsubscribe(session, reader.id, author.id)
    assert visible.id not in [p.id for p in personal_feed(session, reader.id)]
    assert visible.id in [p.id for p in general_feed(session)]
    print("8. После отписки пост исчез только из персональной ленты - ОК")

print("Все сценарии ЛР1 пройдены.")