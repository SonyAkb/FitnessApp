# Схемы архитектуры

| Файл | Что это |
|---|---|
| `fitquest-components.puml` | **Исходник** UML-диаграммы компонентов (PlantUML) — редактируется как текст |
| `fitquest-components.svg` | Читаемое представление (рендер исходника) |

Описание схемы — [`../ARCHITECTURE.md`](../ARCHITECTURE.md), раздел 12.

## Как открыть и изменить

- IntelliJ IDEA / Android Studio — плагин **PlantUML Integration**; VS Code — расширение **PlantUML** (`Alt+D` — предпросмотр).
- Без установки — вставить текст `.puml` на <https://www.plantuml.com/plantuml>.

## Как пересобрать SVG

```bash
# нужен Java 11+ и plantuml.jar (https://github.com/plantuml/plantuml/releases)
java -jar plantuml.jar -tsvg -charset UTF-8 docs/architecture/fitquest-components.puml
```

После правки исходника пересоберите SVG и закоммитьте оба файла.
