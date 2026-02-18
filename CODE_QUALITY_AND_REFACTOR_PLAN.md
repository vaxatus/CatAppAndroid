# Code Quality & Refactor Plan — CatApp

## Implemented (Phase A — done)

- **Vibration**: Fixed duration; use `VibrationEffect.createOneShot(100, DEFAULT_AMPLITUDE)` on API 26+ and `vibrate(100)` on older; use `VibratorManager` on API 31+.
- **NPE safety**: `MainFragment.closeDrawer()` guards on `_binding`; `EffectsController` uses `audio?.` and `vibrator?.`; `ImageViewLogic` null-checks `event`, `mask`, and `imageName`; bounds check for mask pixel access.
- **Deprecated APIs**: `Handler(Looper.getMainLooper())` in ImageViewLogic; display size via `WindowManager.currentWindowMetrics` (API 30+) with fallback to `defaultDisplay.getMetrics` and `resources.displayMetrics`.
- **Cleanups**: Removed debug `println` from SharedPref; renamed `serOptionsAds` → `setOptionsAds`; `ImageHelper.getBitmapFromUri` uses `InputStream.use {}`; `ViewGridAdapter` uses `requireNotNull(context)` and `item.image?.let {}`.
- **ImageViewLogic**: No longer depends on `MainActivity`; uses `Context` and `Activity` only where needed; safe `setImageName(null)` (defaults to `Defaults.DEFAULT_CAT`).

**Still recommended**: Migrate image picker/camera to Activity Result API (Phase A) and Phase B/C when you want better testability and structure.

### Mask / touch logic (dotyk kota = dźwięk)

- **Metoda**: Użycie bitmapy-maski (czarny = obszar kota) jest poprawna i elastyczna dla dowolnych kształtów. Alternatywy (Path hit-test, wiele prostokątów) są możliwe, ale maska dobrze pasuje do nieregularnych obrysów.
- **Poprawki**:
  - Maska jest skaluwana do **rozmiaru widoku** (width × height) i odświeżana w `onSizeChanged` oraz `setImageName`. Współrzędne dotyku (event.x, event.y) są w układzie widoku, więc bezpośrednio odpowiadają pikselom maski — bez błędnego mapowania.
  - Rozpoznawanie „kota”: nie tylko `Color.BLACK`, ale **ciemne piksele** (r,g,b < 80, alpha ≥ 128), żeby uwzględnić antyaliasing masek.
  - Granice: `x`, `y` są ograniczane do `0..width-1` i `0..height-1`, żeby uniknąć wyjątków przy `getPixel`.

---

## 1. Code Quality Assessment

### 1.1 Critical issues (bugs / crashes)

| Issue | Location | Risk | Fix |
|-------|----------|------|-----|
| **Vibration duration** | `EffectsController.startVibrate()` | `vb?.vibrate(100000000000000000)` is invalid (overflow / device-dependent). Can cause no vibration or wrong behavior. | Use `VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE)` on API 26+ and `vibrate(effect)`; fallback for older. |
| **NPE in closeDrawer()** | `MainFragment.closeDrawer()` | Called from `MainActivity.onBackPressed`; if fragment is in destroyed state, `binding` can be null → NPE. | Guard: `_binding ?: return false` at start of `closeDrawer()`. |
| **mask null on touch** | `ImageViewLogic.onTouchEvent` | `mask!!` — if `setImageName` not called or fails, mask can be null → crash on first touch. | Make mask nullable and check before use; or ensure mask is set when image is set. |
| **audio!!** | `EffectsController.setVolumeUp/Down` | If `AudioManager` was null (e.g. context not fully attached), crash. | Use `audio?.adjustStreamVolume(...)` or require non-null in init. |

### 1.2 Null safety

- **EffectsController**: `audio!!` → use safe call or require in init.
- **ImageViewLogic**: `context!!`, `event!!`, `mask!!`, `imageName!!` → use safe calls, early returns, or require.
- **ViewGridAdapter**: `context!!`, `item.image!!` → adapter lifecycle guarantees context; image can be null for placeholder.
- **MainFragment / StartMenuFragment**: `binding get() = _binding!!` → already safe if used only between onViewCreated and onDestroyView; `closeDrawer()` can be called from Activity when view destroyed → guard there.
- **ImageItem**: `name` and `image` are `var` and nullable with no need → make non-null or document.

### 1.3 Deprecated APIs

| API | Location | Replacement |
|-----|----------|-------------|
| `onActivityResult` / `startActivityForResult` | MainFragment, ImageController | Activity Result API: `registerForActivityResult(ActivityResultContracts.PickVisualMedia())` / `TakePicture()`. |
| `onRequestPermissionsResult` | MainFragment, ImageController | Activity Result API: `RequestMultiplePermissions` contract. |
| `Handler()` | ImageViewLogic | `Handler(Looper.getMainLooper())` or `view.postDelayed {}`. |
| `defaultDisplay.getMetrics(displayMetrics)` | ImageViewLogic | `context.display?.getMetrics(displayMetrics)` or `(context as? Activity)?.windowManager?.currentWindowMetrics`. |
| `Context.VIBRATOR_SERVICE` | EffectsController | Prefer `Context.getSystemService(Context.VIBRATOR_SERVICE)` (same) or `VibratorManager` on API 31+. |
| `Vibrator.vibrate(long)` | EffectsController | `VibrationEffect.createOneShot(100, DEFAULT_AMPLITUDE)` + `vibrate(effect)` on API 26+. |
| `FLAG_FULLSCREEN` | MainActivity | Still valid; optional: `WindowInsetsController` for edge-to-edge. |

### 1.4 Architecture & testability

- **Singletons**: `EffectsController`, `AdsController`, `SharedPref` use `getInstance(context)` → hard to test and couple to process. Prefer **Hilt** (or constructor injection) so tests can replace implementations.
- **Tight coupling**: `ImageViewLogic` depends on `MainActivity` and `Activity` → use `Context` and optional callbacks; avoid casting to `MainActivity`.
- **ViewModel empty**: `MainViewModel` has no state or logic → good place to move “selected image”, “vibration enabled” and to drive UI from state.
- **Business logic in views**: Image loading, SharedPref, effects in custom view → move to ViewModel / UseCase and pass state down.
- **No interfaces**: Controllers are concrete classes → introduce interfaces (e.g. `EffectsController` → `SoundAndVibration`) for test doubles.

### 1.5 Naming & small issues

- **serOptionsAds** → **setOptionsAds** (typo).
- **SharedPref**: `init { println("This ($this) is a singleton") }` → remove debug print.
- **ImageHelper.getBitmapFromUri**: use `InputStream?.use { }` for proper close.
- **Permissions**: On API 33+ prefer `READ_MEDIA_IMAGES` and consider **Photo Picker** (`PickVisualMedia`) instead of `ACTION_GET_CONTENT` for better UX and scoped storage.

### 1.6 Functionality quality

- **Image picker / camera**: Works but uses deprecated result API; migration to Activity Result API improves lifecycle safety and future compatibility.
- **Vibration**: Currently broken (wrong duration); fix ensures feature works.
- **Ads**: New API in use; ensure test IDs in debug builds to avoid policy issues.
- **Storage**: Still uses `READ_EXTERNAL_STORAGE`; on API 33+ add `READ_MEDIA_IMAGES` and consider scoped storage only.

---

## 2. Refactor & Modernization Proposals

### Phase A — Quick wins (stability, no architecture change)

1. **Fix vibration**  
   Use `VibrationEffect` on API 26+ and sensible duration (e.g. 100 ms).

2. **Remove NPE risks**  
   - Guard `MainFragment.closeDrawer()` when `_binding == null`.  
   - Replace `audio!!` in EffectsController with safe call or `requireNotNull` after init.  
   - In ImageViewLogic: null-check `mask` and `event`; avoid `!!` where possible.

3. **Fix deprecated APIs (minimal)**  
   - `Handler(Looper.getMainLooper())` or `view.postDelayed` in ImageViewLogic.  
   - Display metrics via `context.display?.getMetrics(...)` or `WindowManager.getCurrentWindowMetrics()` where available.

4. **Typo and cleanup**  
   - Rename `serOptionsAds` → `setOptionsAds`.  
   - Remove `println` from SharedPref.  
   - Use `InputStream?.use { }` in ImageHelper.

5. **Activity Result API**  
   - Replace `startActivityForResult` / `onActivityResult` for image pick and camera with `registerForActivityResult` (PickVisualMedia / TakePicture).  
   - Replace permission request with `RequestMultiplePermissions` contract.  
   This keeps the app working and future-proof.

### Phase B — Better structure (no full rewrite)

6. **MainFragment lifecycle safety**  
   - Don’t call `fragment.closeDrawer()` after fragment is destroyed; or make `closeDrawer()` always safe (guard on `_binding`).

7. **ImageViewLogic**  
   - Don’t depend on `MainActivity`; use `Context` and get `WindowManager`/display from context or callback.  
   - Lazy or lateinit for `effectsController` after context is set.

8. **ImageItem**  
   - Use `data class ImageItem(val name: String, val image: Drawable?)` and ensure adapters handle null drawable (e.g. placeholder).

9. **SharedPref**  
   - Prefer `Context` over `Activity` where only preferences are needed (getSharedPreferences from context).  
   - Optionally migrate to DataStore later.

### Phase C — Architecture (optional, larger)

10. **Dependency injection (Hilt)**  
    - Provide `EffectsController`, `AdsController`, `SharedPref` (or a wrapper) via modules.  
    - Inject into Activity/Fragments and custom views (via factory or constructor where possible).

11. **ViewModel state**  
    - Move “current image name”, “vibration on/off” into MainViewModel; expose StateFlow and update from SharedPref/ImageController.  
    - Fragments observe state and call ViewModel for events.

12. **Interfaces for controllers**  
    - e.g. `SoundAndVibration`, `AdLoader` so tests can substitute implementations.

13. **Navigation Component**  
    - Single Activity with NavController; replace manual fragment transactions and back handling with nav graph and safe back.

---

## 3. Recommended Order

- **Do first**: Phase A (vibration fix, NPE guards, deprecated Handler/Display, typo, Activity Result API, small cleanups).  
- **Next**: Phase B (lifecycle safety, ImageViewLogic decoupling, ImageItem, SharedPref context).  
- **When ready**: Phase C (Hilt, ViewModel state, interfaces, Navigation Component).

This order improves **reliability and functionality** first, then **maintainability and testability**, then **architecture** without breaking the app.
