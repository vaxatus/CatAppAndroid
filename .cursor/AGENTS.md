# Kierunek dla agentów — CatApp

Ten plik jest domyślnym kontekstem dla agentów pracujących nad projektem. **Nowo utworzeni agenci powinni opierać się na oficjalnej dokumentacji i dobrych praktykach wymienionych poniżej.**

## 1. Źródła prawdy w projekcie

| Zasób | Ścieżka | Kiedy czytać |
|-------|---------|--------------|
| Kontrakt API | `.factory/shared/api-contracts.yaml` | Przed pisaniem klienta API, DTO, testów API |
| Modele domenowe | `.factory/shared/data-models.yaml` | Przed definiowaniem modeli / entity / DTO |
| Styl (nazwy, błędy, paginacja, auth) | `.factory/shared/style-guide.json` | Przy nazewnictwie, obsłudze błędów, paginacji |
| Konwencje platform | `.factory/shared/platform-conventions.md` | Przy kodzie Android / iOS / Web / Backend |
| Droid Android | `.factory/droids/android-dev.md` | Przy zmianach w aplikacji Android (architektura, Compose, Kotlin) |
| Architekt | `.factory/droids/project-architect.md` | Przy zmianach cross‑platform i kontraktach |

## 2. Dokumentacja Android (oficjalna)

- **Architektura**: https://developer.android.com/topic/architecture  
  (Guide to app architecture, UI layer, data layer, domain layer)
- **Jetpack Compose**: https://developer.android.com/develop/ui/compose  
  (Compose pathway, API guidelines, state, performance)
- **Compose API guidelines**: https://developer.android.com/develop/ui/compose/api-guidelines  
  (Naming, state hoisting, side effects, modifiers)
- **Quality**: https://developer.android.com/quality  
  (Testing, performance, security)
- **Kotlin na Androidzie**: https://developer.android.com/kotlin  
  (Coroutines, Flow, null safety, idiomy)

Korzystaj z tych adresów przy wyborze wzorców (np. Single Activity, Repository, UDF, Compose) i przy wątpliwościach co do API.

## 3. Dobre praktyki programowania (ogólne)

- **Kotlin**: https://kotlinlang.org/docs/coding-conventions.html  
  (Konwencje nazewnictwa, formatowanie, idiomy)
- **Clean Architecture / warstwy**: domena niezależna od frameworka; UI zależy od domeny, nie odwrotnie.
- **Bezpieczeństwo**: brak wrażliwych danych w kodzie, logach i w odpowiedziach API; tokeny w bezpiecznym storage.
- **Testowalność**: wstrzykiwanie zależności (np. Hilt), interfejsy dla repozytoriów i use case’ów.

## 4. Przepływ pracy przy zmianach

1. **Zmiana API / modeli**  
   Zaktualizuj najpierw `.factory/shared/` (api-contracts.yaml, data-models.yaml, ewentualnie style-guide), potem generuj kod na platformach.
2. **Nowy ekran / feature na Androidzie**  
   Sprawdź `.factory/shared/platform-conventions.md` i `.factory/droids/android-dev.md`; trzymaj się warstw data/domain/presentation i UDF.
3. **Wątpliwości architektoniczne**  
   Odwołaj się do `.factory/droids/project-architect.md` i do dokumentacji Android (linki powyżej).

## 5. Konfiguracja Cursor

- Reguły projektu: `.cursor/rules/` (m.in. `project-and-shared.mdc`, `android-standards.mdc`).
- Konfiguracja projektu: `.cursor-config.json` (odniesienia do AGENTS.md i źródeł dokumentacji).

Nowi agenci powinni być konfigurowani tak, aby domyślnie uwzględniali ten plik (AGENTS.md) oraz powyższe źródła dokumentacji i dobrych praktyk.
