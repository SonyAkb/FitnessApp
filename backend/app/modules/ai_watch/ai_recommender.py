"""
Заглушка ИИ-модуля. Сейчас — простое правило (rule-based), чтобы MVP работал
без реальной модели.

TODO(module-6):
  1. Обучить лёгкую модель в Google Colab (ai/colab_notebook.ipynb) —
     например, классификатор "нужен ли лёгкий/тяжёлый день" по истории тренировок,
     или простая content-based рекомендация следующего плана.
  2. Экспортировать модель (pickle/onnx/веса) и положить в backend/app/modules/ai_watch/model/.
  3. Заменить rule_based_recommend(...) на реальный inference.
     Если модель тяжелее — можно временно держать её отдельным сервисом
     (например, эндпоинт в Colab + ngrok) и дергать через httpx.
"""


def rule_based_recommend(completed_workouts_last_7_days: int) -> dict:
    if completed_workouts_last_7_days == 0:
        return {
            "recommendation": "Лёгкая разминка 15 минут",
            "reason": "На этой неделе пока не было тренировок — начнём с малого.",
        }
    if completed_workouts_last_7_days < 3:
        return {
            "recommendation": "Тренировка средней интенсивности",
            "reason": "Хороший темп, но есть куда расти в этой неделе.",
        }
    return {
        "recommendation": "День отдыха или лёгкая растяжка",
        "reason": "Уже много тренировок за неделю — дайте телу восстановиться.",
    }
