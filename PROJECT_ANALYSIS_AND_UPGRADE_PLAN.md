# Analiza projektu CatApp i plan upgrade do najnowszych standardów

Dokument powstał na podstawie `.factory` i stanu repozytorium. Ma służyć jako mapa drogowa migracji do współczesnego stosu Android (AndroidX, Jetpack Compose, Clean Architecture) oraz jako wskazówka dla agentów — oparcie o dokumentację Androida i dobre praktyki.

---

## 1. Stan obecny — analiza

### 1.1 Build i SDK

| Element | Obecny stan | Uwagi |
|--------|-------------|--------|
| **compileSdkVersion** | 27 | Bardzo stary (Android 8.1). Docelowo 35 (lub aktualny latest). |
| **minSdkVersion** | 19 | Można podnieść do 24+ przy modernizacji (Compose ma min 24). |
| **targetSdkVersion** | 27 | Wymagane przez sklep docelowo 34+. |
| **Gradle** | 4.6 (wrapper) | Za stary. Docelowo 8.x. |
| **AGP** | 3.2.1 | Docelowo 8.x. |
| **Kotlin** | 1.2.51 | Docelowo 2.0.x. |

### 1.2 Biblioteki

- **Android Support Library** (appcompat-v7, design, constraint-layout, lifecycle:extensions 1.1.1) — **nie AndroidX**. Wszystkie te API są zdeprecjonowane; standardem jest AndroidX.
- **JUnit 4** — docelowo JUnit 5 (Jupiter) + MockK.
- **Espresso** — można zostawić lub uzupełnić testami Compose.
- **Play Services Ads 17.0.0** — do aktualizacji do bieżącej wersji.
- **Kotlin Android Extensions** (`kotlin-android-extensions`) — **zdeprecjonowane** (synthetics); zastąpić View Binding lub Compose.
- Brak: **Hilt**, **Retrofit**, **Kotlin Serialization**, **Jetpack Compose**, **Navigation Component**, **Version Catalog**.

### 1.3 Architektura i kod

- **Struktura pakietów**: płaska pod `com.vaxatus.cat.myapplication` z `ui/main`, `ui/logic` — **brak** wyraźnych warstw `data/`, `domain/`, `presentation/` z Clean Architecture.
- **UI**: XML layouts + **Fragments** + `ViewModel` (arch lifecycle 1.1.1). Brak Compose.
- **ViewModel**: `android.arch.lifecycle.ViewModel` (stary artifact), prawie pusty; brak `StateFlow`/UDF.
- **MainActivity**: `AppCompatActivity`, `supportFragmentManager`, `onBackPressed()` (deprecated), ręczna obsługa fragmentów.
- **Singleton**: `EffectsController.getInstance()`, `AdsController.getInstance()` — zamiast DI (np. Hilt).
- **Kotlin synthetics**: `kotlinx.android.synthetic.main.main_fragment.*` — do usunięcia.
- **Testy**: przykładowe JUnit 4 i Espresso; brak testów jednostkowych dla ViewModel/Flow i testów Compose.

### 1.4 Zgodność z .factory

- **platform-conventions.md**: wymaga MVVM + Clean Architecture (data/domain/presentation), UDF, Repository, UseCase, Compose (PascalCase composables, LazyColumn, Material 3), Hilt, Version Catalog — **obecny kod nie spełnia**.
- **style-guide.json** / **api-contracts.yaml** / **data-models.yaml**: aplikacja obecnie nie korzysta z backendu z tego kontraktu; przy dodawaniu API trzeba będzie generować kod zgodnie z `.factory/shared/`.
- **android-dev.md**: opisuje docelową strukturę katalogów i wzorce; upgrade ma zbliżyć projekt do tego opisu.

---

## 2. Plan upgrade — etapy

Cel: doprowadzić aplikację do stanu zgodnego z `.factory/shared/platform-conventions.md` i `.factory/droids/android-dev.md`, z oparciem o oficjalną dokumentację Androida i dobre praktyki (patrz `.cursor/AGENTS.md`).

### Faza 0: Przygotowanie (bez zmiany zachowania)

1. **Version Catalog**  
   Dodać `gradle/libs.versions.toml` i przenieść wersje Kotlin, AGP, bibliotek do katalogu; w `build.gradle` użyć `libs.xxx.get()`.
2. **Backup i branch**  
   Branch typu `upgrade/modern-stack`; możliwość łatwego cofnięcia.

### Faza 1: Migracja na współczesny build (AndroidX, Gradle, Kotlin)

3. **Gradle**  
   - Upgrade wrapper do Gradle 8.x (np. 8.5).  
   - Upgrade AGP do 8.x.  
   - Upgrade Kotlin do 2.0.x.  
   - Usunąć `jcenter()`; używać `mavenCentral()` (i ewentualnie `google()`).
4. **AndroidX**  
   - Włączyć migrację AndroidX (np. `android.useAndroidX=true`, `android.enableJetifier=true` w `gradle.properties`).  
   - Zamienić wszystkie importy `android.support.*` i `android.arch.*` na `androidx.*`.  
   - Zaktualizować zależności do wersji AndroidX (np. `appcompat`, `material`, `constraintlayout`, `lifecycle-*`).
5. **SDK**  
   - `compileSdk` / `targetSdk` przynajmniej 34 (lub aktualny).  
   - `minSdk` na razie można zostawić (np. 21 lub 24), z myślą o Compose min 24.
6. **Kotlin**  
   - Usunąć `kotlin-android-extensions`.  
   - Włączyć View Binding (`buildFeatures { viewBinding true }`) we wszystkich modułach z XML layouts.
7. **Test runner**  
   - Zamienić na `androidx.test.runner.AndroidJUnitRunner` i ustawić JUnit 4/5 zgodnie z nowymi testami.

**Weryfikacja**: build przechodzi, aplikacja się uruchamia, brak regresji w podstawowych flow (np. start, galeria, reklamy).

### Faza 2: Dependency Injection i warstwy

8. **Hilt**  
   - Dodać Hilt (wersja z Version Catalog).  
   - `Application` z `@HiltAndroidApp`.  
   - Zamienić singletony (`EffectsController`, `AdsController`, itd.) na `@Inject` / `@Singleton` w modułach; wstrzykiwać tam, gdzie używane.
9. **Struktura pakietów (Clean Architecture)**  
   - Bez zmiany jeszcze na Compose: wydzielić pakiety `data/`, `domain/`, `presentation/` pod `com.vaxatus.cat.myapplication`.  
   - Przenieść istniejące klasy: np. modele do `domain/model`, repozytoria (jeśli pojawią się) do `data/repository` i `domain/repository`, ViewModele do `presentation/screens/...`.  
   - Zachować kompatybilność z obecnymi Fragmentami i View Binding.

**Weryfikacja**: DI działa, brak `getInstance()`, struktura katalogów zgodna z konwencją z `.factory`.

### Faza 3: Nawigacja i ViewModel (UDF)

10. **Navigation Component**  
    - Dodać `androidx.navigation:navigation-fragment-ktx` (i fragment, UI).  
    - Jedna Activity (MainActivity) + nawigacja między ekranami (np. start menu ↔ main/gallery).  
    - Zamienić ręczne `supportFragmentManager.beginTransaction()...` na NavController i graph.
11. **onBackPressed**  
    - Zastąpić przez `OnBackPressedDispatcher` / `OnBackCallback` (lub odpowiednik w Navigation).
12. **ViewModel + UDF**  
    - ViewModele: `androidx.lifecycle.ViewModel` (z lifecycle).  
    - Stan ekranu: `StateFlow<UiState>` (sealed class/interface: Loading, Success, Error).  
    - Zdarzenia: metody w ViewModel (np. `onItemClick`, `onRefresh`) zamiast callbacków z Fragmentów.  
    - W Fragmentach: tylko `viewModel.uiState.collectAsStateWithLifecycle()` (lub `observe`) i wywołania metod ViewModel.

**Weryfikacja**: Nawigacja działa, back stack poprawny, stan ekranu w jednym miejscu (ViewModel).

### Faza 4: Jetpack Compose (opcjonalnie, stopniowo)

13. **Włączenie Compose**  
    - `minSdk` co najmniej 24.  
    - Dodać zależności Compose (BOM), `ComposeCompiler` (zgodnie z wersją Kotlin).  
    - W MainActivity: `setContent { CatAppTheme { ... } }` z NavHost; pierwszy ekran może być w Compose lub Fragment w Compose (interop).
14. **Migracja ekranów**  
    - Jeden ekran na raz: np. Start Menu → Composable; potem Main/Gallery.  
    - Composable w PascalCase, stan z ViewModel przez `collectAsStateWithLifecycle()`, listy przez `LazyColumn`/`LazyRow` z `key`.  
    - Material 3, `MaterialTheme`, dark mode.
15. **Usunięcie XML**  
    - Po przeniesieniu wszystkich ekranów do Compose — usunąć nieużywane layouty i wyłączyć View Binding w tych modułach.

**Weryfikacja**: Aplikacja w pełni w Compose (lub hybrydowo), zgodność z API guidelines z dokumentacji.

### Faza 5: Sieć i kontrakt (.factory)

16. **API (gdy będzie backend)**  
    - Czytać `.factory/shared/api-contracts.yaml` i `data-models.yaml`.  
    - Wygenerować/dopisać interfejsy Retrofit i DTO (Kotlin Serialization/Moshi) zgodne z kontraktem.  
    - Repozytoria w `data/repository` wywołują API; UseCase w `domain/usecase` wywołują repozytoria.  
    - Style: `style-guide.json` (błędy RFC 7807, paginacja, auth).
17. **Konfiguracja**  
    - Base URL z buildConfig / BuildType / env — bez hardkodowania.

### Faza 6: Jakość i testy

18. **Testy jednostkowe**  
    - JUnit 5 + MockK.  
    - ViewModele: testy `StateFlow` (np. Turbine).  
    - UseCase’y i repozytoria: mocki interfejsów.
19. **Testy UI**  
    - Compose: `createComposeRule()`, `onNodeWithText`, itd.  
    - Ewentualnie: Paparazzi/Roborazzi dla screenshotów.
20. **Lint / detekt**  
    - Włączyć strict mode; usuwać deprecacje zgłaszane przez IDE.

---

## 3. Priorytety i ryzyko

- **Priorytet wysoki**: Faza 1 (build, AndroidX, View Binding) — bez tego dalszy upgrade jest trudny.  
- **Średni**: Faza 2 (Hilt, struktura) i Faza 3 (Navigation, UDF) — stabilna baza pod nowe funkcje.  
- **Niższy**: Faza 4 (Compose) — można robić stopniowo; Faza 5 gdy pojawi się backend; Faza 6 równolegle.

**Ryzyko**: duża zmiana w jednym kroku. Dlatego fazy są rozbite na małe kroki z weryfikacją (build, uruchomienie, podstawowe flow).

---

## 4. Kierowanie agentów

- **Nowi agenci** powinni być kierowani na:  
  - `.cursor/AGENTS.md` (źródła w projekcie + linki do dokumentacji).  
  - `.factory/shared/platform-conventions.md` i `.factory/droids/android-dev.md` przy zmianach w Androidzie.  
  - Oficjalną dokumentację: https://developer.android.com (Architecture, Compose, Quality), https://kotlinlang.org/docs/coding-conventions.html.
- **Konfiguracja Cursor**: `.cursor/rules/` (project-and-shared.mdc, android-standards.mdc) oraz `.cursor-config.json` — zapewniają spójność z `.factory` i z dobrymi praktykami.

---

## 5. Podsumowanie

| Obszar | Teraz | Docelowo |
|--------|--------|----------|
| Build | Gradle 4.6, AGP 3.2, Kotlin 1.2 | Gradle 8.x, AGP 8.x, Kotlin 2.0 |
| UI | Support Library, Fragments, XML, synthetics | AndroidX, (Compose), View Binding / Compose |
| Architektura | Płaska, singletony | data/domain/presentation, Hilt, UDF |
| Nawigacja | Ręczne Fragment transactions | Navigation Component |
| Stan | Pusty ViewModel, callbacki | StateFlow, sealed UiState |
| API | Brak / ad‑hoc | Retrofit + .factory shared contract |
| Testy | JUnit 4, podstawowe | JUnit 5, MockK, Turbine, Compose testing |

Realizacja planu krok po kroku, z testami i weryfikacją po każdej fazie, pozwoli doprowadzić CatApp do najnowszych standardów i do zgodności z konfiguracją `.factory` oraz z dokumentacją i dobrymi praktykami opisanymi w AGENTS.md.
