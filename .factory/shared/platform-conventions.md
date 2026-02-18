# Platform Conventions — All Droids Must Follow These

## Cross-Platform Rules (MANDATORY)

1. **API contract is the source of truth** — read `api-contracts.yaml` before generating any API-related code
2. **Domain models are shared** — read `data-models.yaml` before creating any model/entity/DTO
3. **Style guide is enforced** — read `style-guide.json` for naming, errors, pagination, auth, dates, i18n
4. **Never hardcode API URLs** — use environment/config injection on every platform
5. **Never expose internal IDs** — use UUIDs in APIs, keep auto-increment IDs internal to DB
6. **All API errors follow RFC 7807** — Problem Details format with machine-readable `code` field
7. **Dates are always UTC in storage and API** — client converts to local timezone for display
8. **Backend returns error CODES, not translated messages** — client handles i18n
9. **Sensitive data (passwords, tokens, keys) never in logs, never in API responses, never in git**

## Android / Kotlin Conventions

### Architecture (Google Official + Clean Architecture)
- **MVVM + Clean Architecture**: 3 layers — `data/`, `domain/`, `presentation/`
- **Unidirectional Data Flow (UDF)**: State flows DOWN (ViewModel → UI), events flow UP (UI → ViewModel)
- **Single Activity**: Navigation Component or Compose Navigation
- **Repository Pattern**: Data layer exposes repositories; UI never touches data sources directly
- **UseCases**: Business logic in `domain/usecase/` — one class per operation

### Jetpack Compose (Google Official Guidelines)
- Composable functions: `@Composable` naming in PascalCase (e.g., `UserProfileScreen`)
- State hoisting: lift state to the nearest shared ancestor
- Use `remember { mutableStateOf() }` for local state, `StateFlow` from ViewModel for screen state
- Material 3 theming with dynamic colors support
- `LazyColumn`/`LazyRow` for lists (never `Column` with `forEach` for large lists)
- Side effects: `LaunchedEffect`, `DisposableEffect`, `SideEffect` — never call suspend in composition
- Slot-based APIs: accept `@Composable () -> Unit` parameters for flexible composition

### Kotlin Best Practices
- Coroutines + Flow for all async operations (never callbacks, never RxJava in new code)
- Sealed classes/interfaces for UI state modeling: `sealed interface UiState { data class Success(...), data object Loading, data class Error(...) }`
- Null safety: avoid `!!`, use `?.let`, `?:`, `requireNotNull()`
- `data class` for DTOs and domain models
- Extension functions for utilities (keep them focused, don't abuse)
- Hilt for DI — `@HiltViewModel`, `@Inject`, `@Module` with `@Provides`
- Version Catalogs (`libs.versions.toml`) for dependency management

### Networking
- Retrofit + OkHttp with interceptors for auth token injection
- Kotlin Serialization (preferred) or Moshi for JSON parsing
- Model: `ApiResponse<T>` wrapper or sealed class for network results
- Certificate pinning for production

### Testing
- JUnit 5 + MockK + Turbine (Flow testing)
- Compose Testing: `createComposeRule()`, `onNodeWithText()`, semantic matchers
- Screenshot tests: Paparazzi (no device needed) or Roborazzi

---

## iOS / Swift Conventions

### Architecture (Apple Official + Best Practices)
- **MVVM with SwiftUI** or **The Composable Architecture (TCA)** for complex apps
- **Protocol-Oriented Programming**: abstractions via protocols, not base classes
- **Repository Pattern**: same as Android — data layer behind protocol interfaces
- Proper layer separation: `View → ViewModel → Repository → DataSource`

### SwiftUI (Apple HIG + WWDC Best Practices)
- Views are lightweight value types — keep them small and composable
- State management hierarchy: `@State` (local) → `@Binding` (parent-child) → `@StateObject`/`@ObservedObject` (ViewModel) → `@EnvironmentObject` (global)
- `@Observable` macro for iOS 17+ (preferred over ObservableObject)
- `NavigationStack` + `NavigationPath` for navigation (not deprecated `NavigationView`)
- `LazyVStack`/`LazyHStack` inside `ScrollView` for performance
- Accessibility: `.accessibilityLabel()`, `.accessibilityHint()`, Dynamic Type support
- Preview-driven development: write `#Preview {}` for every view with multiple states

### Swift Best Practices
- Swift Concurrency: `async/await`, actors, `Task {}`, structured concurrency
- Value types (struct, enum) preferred over reference types (class)
- `Codable` for all API models with `CodingKeys` when JSON naming differs
- Error handling: typed throws, `Result<Success, Failure>`, avoid force-unwrapping
- Generics + associated types for protocol-based abstractions
- Swift API Design Guidelines: clarity at point of use, no abbreviations, verb phrases for mutating methods

### Networking
- `URLSession` with `async/await` (or Alamofire if project already uses it)
- Codable models matching `api-contracts.yaml` schemas
- `HTTPClient` protocol for testability
- Keychain for token storage (never UserDefaults for sensitive data)

### Testing
- Swift Testing framework (`@Test`, `#expect`) for new code, XCTest for existing
- Protocol-based mocking (create `MockUserRepository: UserRepositoryProtocol`)
- swift-snapshot-testing for UI regression
- `@MainActor` aware tests for UI-bound code

---

## Web / React / TypeScript Conventions

### Architecture
- **Next.js** with App Router (or Vite + React Router for SPAs)
- **Feature-based folder structure**: `src/features/<feature>/` with components, hooks, api, types
- **Monorepo support**: Turborepo or Nx with shared packages (`packages/ui`, `packages/api-client`, `packages/types`)
- **Server Components** (Next.js): default to server, use `'use client'` only when needed

### React Best Practices (Airbnb + Official Docs)
- Functional components only (no class components in new code)
- Custom hooks for reusable logic: `useAuth()`, `useProducts()`, `usePagination()`
- React Query / TanStack Query for server state (not Redux for API data)
- Zustand or Jotai for client state (or Context for simple cases)
- Component composition over prop drilling — use `children`, render props, compound components
- `React.memo()` only when measurably needed (profile first)
- Error boundaries for graceful failure handling
- Suspense + lazy loading for code splitting

### TypeScript Best Practices
- `strict: true` in tsconfig, no `any` types (use `unknown` if truly unknown)
- `interface` for object shapes, `type` for unions/intersections/utility types
- Discriminated unions for state modeling: `type State = { status: 'loading' } | { status: 'success', data: T } | { status: 'error', error: string }`
- Zod for runtime validation (API responses, form inputs) with `.infer<>` for type extraction
- No `as` type assertions unless absolutely necessary (prefer type guards)
- Barrel exports (`index.ts`) for public API of each module

### Styling
- Tailwind CSS (preferred) or CSS Modules
- Component library: shadcn/ui (Radix primitives) or MUI
- Mobile-first responsive design (`sm:`, `md:`, `lg:` breakpoints)
- CSS variables for theming (light/dark mode)
- No inline styles except dynamic values

### Testing
- Vitest (preferred) or Jest for unit tests
- React Testing Library for component tests (test behavior, not implementation)
- Playwright for E2E (see ui-test-droid)
- MSW (Mock Service Worker) for API mocking in tests and Storybook

---

## Backend Conventions (Spring Boot / Node.js / FastAPI)

### General Backend Rules
- **Layered architecture**: Controller/Router → Service → Repository → Database
- **DTOs separate from entities**: never expose database entities directly in API responses
- **Input validation at the boundary**: validate in controller/router before passing to service
- **Business logic in service layer**: controllers are thin, services contain logic
- **Repository pattern**: abstract database access behind interfaces
- **Idempotency**: POST operations should be idempotent with idempotency keys where possible

### Spring Boot (Kotlin)
- `@RestController` + `@RequestMapping("/api/v1/...")`
- `@Service`, `@Repository` stereotypes with constructor injection
- `data class` for DTOs, `@Entity` for JPA entities (separate classes)
- Flyway or Liquibase for database migrations (never manual DDL)
- Spring Security with JWT filter chain
- `@Transactional` at service layer
- `@ControllerAdvice` for global exception handling → RFC 7807 responses
- Spring Actuator for health checks and metrics
- Testcontainers for integration tests

### Node.js (NestJS / Express + TypeScript)
- NestJS preferred for structured apps (modules, DI, decorators)
- Feature-based modules: `src/modules/<feature>/` with controller, service, dto, entity
- Class-validator + class-transformer for DTO validation
- TypeORM or Prisma for database access
- Passport.js or custom JWT guard for auth
- Global exception filter for RFC 7807 responses
- Pino or Winston for structured JSON logging

### Python (FastAPI)
- Domain-driven project structure: `app/domains/<feature>/`
- Pydantic v2 models for request/response schemas (BaseModel)
- SQLAlchemy 2.0 + Alembic for database + migrations
- Dependency injection via FastAPI `Depends()`
- `HTTPException` with RFC 7807-style detail bodies
- Async-first: `async def` endpoints, `asyncpg` for database

---

## Database / PostgreSQL Conventions

### Schema Design
- `snake_case` for all table and column names
- Plural table names: `users`, `products`, `recipes`, `recipe_ingredients`
- UUID primary keys (UUIDv7 preferred for time-sortable)
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` on every table
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` on every table (with trigger)
- Foreign keys always have indexes
- Soft delete with `deleted_at TIMESTAMPTZ NULL` (not boolean)
- `NOT NULL` by default — only nullable when business logic requires it

### Migrations
- Forward-only migrations (never edit existing migrations)
- Zero-downtime migrations: add nullable column → backfill → add constraint
- Name convention: `V001__create_users_table.sql` or timestamp-based
- Always include rollback/down migration

### Performance
- Index frequently queried columns (especially foreign keys, search fields)
- Composite indexes for multi-column queries (order matters: most selective first)
- `EXPLAIN ANALYZE` before deploying new queries
- Connection pooling (PgBouncer or built-in pool in ORM)
- Avoid `SELECT *` — always specify columns
- Use `LIMIT` + cursor-based pagination for large tables
