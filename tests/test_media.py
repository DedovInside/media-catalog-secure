from fastapi.testclient import TestClient


class TestMediaAPI:
    """Тесты для /media эндпоинтов"""

    def test_get_empty_media_list(self, client: TestClient):
        """Тест получения пустого списка медиа"""
        response = client.get("/media")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_media_success(self, client: TestClient):
        """Тест успешного создания медиа"""
        media_data = {
            "title": "The Rock",
            "kind": "movie",
            "year": 1996,
            "description": "Action-packed thriller",
        }

        response = client.post("/media", json=media_data)
        assert response.status_code == 201

        created_media = response.json()
        assert created_media["title"] == "The Rock"
        assert created_media["kind"] == "movie"
        assert created_media["year"] == 1996
        assert created_media["status"] == "to_watch"
        assert created_media["rating"] is None
        assert "id" in created_media
        assert "created_at" in created_media

    def test_get_media_list_after_creation(self, client: TestClient):
        """Тест получения списка медиа после создания"""
        # Создаем два медиа
        media1 = {
            "title": "The Lord of the Rings: The Return of the King",
            "kind": "movie",
            "year": 2003,
        }
        media2 = {"title": "BlockChain Course", "kind": "course", "year": 2025}

        client.post("/media", json=media1)
        client.post("/media", json=media2)

        response = client.get("/media")
        assert response.status_code == 200

        media_list = response.json()
        assert len(media_list) == 2

        titles = [media["title"] for media in media_list]
        assert "The Lord of the Rings: The Return of the King" in titles
        assert "BlockChain Course" in titles

    def test_get_media_by_id_success(self, client: TestClient):
        """Тест получения медиа по ID"""
        # Создаем медиа
        create_response = client.post(
            "/media", json={"title": "Test Movie", "kind": "movie", "year": 2025}
        )
        media_id = create_response.json()["id"]

        # Получаем по ID
        response = client.get(f"/media/{media_id}")
        assert response.status_code == 200

        media = response.json()
        assert media["id"] == media_id
        assert media["title"] == "Test Movie"

    def test_get_media_by_id_not_found(self, client: TestClient):
        """Тест получения несуществующего медиа"""
        response = client.get("/media/999")
        assert response.status_code == 404

        error = response.json()
        # RFC 7807 структура
        assert "type" in error
        assert "title" in error
        assert "status" in error
        assert "detail" in error
        assert "correlation_id" in error

        # Безопасное сообщение
        assert error["detail"] == "The requested resource could not be found"
        assert "999" not in error["detail"]  # ID НЕ РАСКРЫВАЕТСЯ

    def test_create_duplicate_media(self, client: TestClient):
        """Тест создания дублирующего медиа"""
        media_data = {
            "title": "Indiana Jones and the Last Crusade",
            "kind": "movie",
            "year": 1989,
        }

        # Создаем первое медиа
        response1 = client.post("/media", json=media_data)
        assert response1.status_code == 201

        # Пытаемся создать дубликат
        response2 = client.post("/media", json=media_data)
        assert response2.status_code == 409

        error = response2.json()
        # RFC 7807 структура
        assert "type" in error
        assert "status" in error
        assert "detail" in error
        assert "correlation_id" in error

        # Безопасное сообщение
        assert error["detail"] == "A resource with these properties already exists"
        assert "Indiana Jones" not in error["detail"]  # DATA НЕ РАСКРЫВАЕТСЯ

    def test_filter_media_by_kind(self, client: TestClient):
        """Тест фильтрации медиа по типу"""
        # Создаем медиа разных типов
        client.post("/media", json={"title": "Movie 1", "kind": "movie", "year": 2020})
        client.post(
            "/media", json={"title": "Course 1", "kind": "course", "year": 2021}
        )
        client.post("/media", json={"title": "Movie 2", "kind": "movie", "year": 2022})

        # Фильтруем по типу movie
        response = client.get("/media?kind=movie")
        assert response.status_code == 200

        media_list = response.json()
        assert len(media_list) == 2

        # Проверяем, что все медиа - фильмы
        for media in media_list:
            assert media["kind"] == "movie"

        # Проверяем конкретные названия
        titles = [media["title"] for media in media_list]
        assert "Movie 1" in titles
        assert "Movie 2" in titles

    def test_filter_media_by_status(self, client: TestClient):
        """Тест фильтрации медиа по статусу"""
        # Создаем медиа
        create_response = client.post(
            "/media", json={"title": "Test Movie", "kind": "movie", "year": 2023}
        )
        media_id = create_response.json()["id"]

        # Меняем статус на watched
        client.patch(
            f"/media/{media_id}/status", json={"status": "watched", "rating": 8}
        )

        # Фильтруем по статусу watched
        response = client.get("/media?status=watched")
        assert response.status_code == 200

        media_list = response.json()
        assert len(media_list) == 1
        assert media_list[0]["status"] == "watched"
        assert media_list[0]["rating"] == 8

    def test_update_media_success(self, client: TestClient):
        """Тест обновления медиа"""
        # Создаем медиа
        create_response = client.post(
            "/media", json={"title": "Original Title", "kind": "movie", "year": 2020}
        )
        media_id = create_response.json()["id"]

        # Обновляем
        update_data = {
            "title": "Updated Title",
            "kind": "series",
            "year": 2021,
            "description": "Updated description",
        }

        response = client.put(f"/media/{media_id}", json=update_data)
        assert response.status_code == 200

        updated_media = response.json()
        assert updated_media["title"] == "Updated Title"
        assert updated_media["kind"] == "series"
        assert updated_media["year"] == 2021
        assert updated_media["description"] == "Updated description"
        assert updated_media["id"] == media_id  # ID не должен измениться

    def test_update_media_status_success(self, client: TestClient):
        """Тест обновления статуса медиа"""
        # Создаем медиа
        create_response = client.post(
            "/media", json={"title": "Test Movie", "kind": "movie", "year": 2023}
        )
        media_id = create_response.json()["id"]

        # Обновляем статус
        status_update = {"status": "watched", "rating": 9}

        response = client.patch(f"/media/{media_id}/status", json=status_update)
        assert response.status_code == 200

        updated_media = response.json()
        assert updated_media["status"] == "watched"
        assert updated_media["rating"] == 9
        assert updated_media["title"] == "Test Movie"  # Остальные поля не изменились

    def test_delete_media_success(self, client: TestClient):
        """Тест удаления медиа"""
        # Создаем медиа
        create_response = client.post(
            "/media", json={"title": "To Delete", "kind": "movie", "year": 2023}
        )
        media_id = create_response.json()["id"]

        # Удаляем
        delete_response = client.delete(f"/media/{media_id}")
        assert delete_response.status_code == 204

        # Проверяем, что медиа действительно удалено
        get_response = client.get(f"/media/{media_id}")
        assert get_response.status_code == 404

    def test_delete_media_not_found(self, client: TestClient):
        """Тест удаления несуществующего медиа"""
        response = client.delete("/media/999")
        assert response.status_code == 404

        error = response.json()
        # ✅ RFC 7807 структура
        assert error["detail"] == "The requested resource could not be found"
        assert "999" not in error["detail"]


class TestMediaValidation:
    """Тесты валидации данных медиа"""

    def test_create_media_invalid_year_future(self, client: TestClient):
        """Тест создания медиа с годом из будущего"""
        media_data = {
            "title": "Future Movie",
            "kind": "movie",
            "year": 2050,  # Превышает максимум 2030
        }

        response = client.post("/media", json=media_data)
        assert response.status_code == 422  # Validation error

    def test_create_media_invalid_year_past(self, client: TestClient):
        """Тест создания медиа с очень старым годом"""
        media_data = {
            "title": "Ancient Movie",
            "kind": "movie",
            "year": 1700,  # Меньше минимума 1800
        }

        response = client.post("/media", json=media_data)
        assert response.status_code == 422  # Validation error

    def test_create_media_empty_title(self, client: TestClient):
        """Тест создания медиа с пустым названием"""
        media_data = {"title": "", "kind": "movie", "year": 2020}  # Пустое название

        response = client.post("/media", json=media_data)
        assert response.status_code == 422  # Validation error

    def test_create_media_invalid_kind(self, client: TestClient):
        """Тест создания медиа с неверным типом"""
        media_data = {
            "title": "Test Movie",
            "kind": "invalid_kind",  # Неверный тип
            "year": 2020,
        }

        response = client.post("/media", json=media_data)
        assert response.status_code == 422  # Validation error


class TestMediaIntegration:
    """Интеграционные тесты полного жизненного цикла"""

    def test_full_media_lifecycle(self, client: TestClient):
        """Тест полного жизненного цикла медиа"""
        # 1. Создание медиа
        media_data = {
            "title": "Forrest Gump",
            "kind": "movie",
            "year": 1994,
            "description": "Life is like a box of chocolates.",
        }

        create_response = client.post("/media", json=media_data)
        assert create_response.status_code == 201
        media_id = create_response.json()["id"]

        # 2. Получение по ID
        get_response = client.get(f"/media/{media_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Forrest Gump"

        # 3. Обновление статуса на "watching"
        status_response = client.patch(
            f"/media/{media_id}/status", json={"status": "watching"}
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "watching"

        # 4. Обновление информации о медиа
        update_response = client.put(
            f"/media/{media_id}",
            json={
                "title": "Updated Forrest Gump",
                "kind": "movie",
                "year": 1994,
                "description": "Sweet home Alabama.",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Forrest Gump"

        # 5. Финальное обновление статуса на "watched" с рейтингом
        final_status_response = client.patch(
            f"/media/{media_id}/status", json={"status": "watched", "rating": 8}
        )
        assert final_status_response.status_code == 200
        final_media = final_status_response.json()
        assert final_media["status"] == "watched"
        assert final_media["rating"] == 8

        # 6. Проверяем, что медиа в списке
        list_response = client.get("/media")
        assert list_response.status_code == 200
        media_list = list_response.json()
        assert len(media_list) == 1
        assert media_list[0]["id"] == media_id

        # 7. Удаление медиа
        delete_response = client.delete(f"/media/{media_id}")
        assert delete_response.status_code == 204

        # 8. Проверяем, что медиа удалено
        final_get_response = client.get(f"/media/{media_id}")
        assert final_get_response.status_code == 404

        # 9. Проверяем, что список пуст
        final_list_response = client.get("/media")
        assert final_list_response.status_code == 200
        # Проверяем что наш media_id отсутствует
        final_media_list = final_list_response.json()
        media_ids = [media["id"] for media in final_media_list]
        assert media_id not in media_ids  # Наше медиа должно быть удалено
