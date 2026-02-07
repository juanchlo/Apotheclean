---
trigger: always_on
---

# Frontend Guidelines – Apotheclean

## Propósito

Este documento define el estilo visual, las reglas de diseño y el alcance funcional del **frontend de Apotheclean**.

El backend ya está implementado en Flask.  
El frontend **solo debe consumir los endpoints existentes** y **no debe implementar ni duplicar lógica de negocio**.

El objetivo es construir una aplicación en React limpia, moderna y consistente, priorizando claridad, usabilidad y mantenibilidad.

---

## Stack Tecnológico

- React
- Node.js
- JavaScript o TypeScript (TypeScript preferido)
- API REST (backend en Flask)
- Autenticación JWT
- Librería de gráficos (Recharts, Chart.js o equivalente)

---

## Identidad Visual

### Tipografía

- Fuente principal: **Inter**
- Fallbacks: `system-ui`, `-apple-system`, `Segoe UI`, `Roboto`, `sans-serif`

Reglas de uso:
- Títulos: peso medium o semi-bold
- Texto base: regular
- Evitar el uso excesivo de variantes de peso
- Mantener una jerarquía clara entre títulos, subtítulos, labels y texto

---

### Paleta de Colores

Usar una paleta sobria y profesional con un único color de acento.

**Colores Base**
- Fondo principal: `#FFFFFF`
- Texto principal: `#0F172A`
- Texto secundario: `#475569`

**Color de Acento**
- Acento principal: `#4F46E5`
- Acento hover: `#4338CA`

**Colores Neutros UI**
- Bordes: `#E5E7EB`
- Fondos suaves / secciones: `#F8FAFC`
- Texto e íconos deshabilitados: `#94A3B8`

**Colores de Estado**
- Éxito: `#16A34A`
- Advertencia: `#D97706`
- Error: `#DC2626`

Reglas:
- El color de acento se usa solo para acciones primarias y elementos clave.
- No usar múltiples colores de acento.
- Garantizar contraste suficiente para accesibilidad.

---

### Formas, Espaciado y Profundidad

- Border radius estándar: 8–12px
- Cards y modales con sombras sutiles:
  - Ejemplo: `0 4px 12px rgba(0, 0, 0, 0.05)`
- Evitar bordes duros; preferir separación por espacio y sombra.
- Espaciado consistente:
  - Pequeño: 8px
  - Medio: 16px
  - Grande: 24–32px

---

### Movimiento e Interacción

- Transiciones suaves y discretas
- Hover:
  - Cambios sutiles de fondo o elevación
- Evitar animaciones llamativas o innecesarias
- El movimiento debe comunicar estado, no decorar

---

## Principios de UX

- Separación clara entre **Portal de Usuario** y **Portal de Administrador**
- Navegación predecible
- Jerarquía visual clara en todas las pantallas
- Feedback explícito para:
  - Carga
  - Errores
  - Estados vacíos
- Paginación y filtros deben reflejar exactamente el comportamiento del backend

---

## Estructura de la Aplicación (Recomendada)
src/
├── api/
│ ├── client.js
│ ├── auth.api.js
│ ├── products.api.js
│ ├── sales.api.js
│
├── hooks/
│ ├── useAuth.js
│ ├── useProducts.js
│ ├── useSales.js
│
├── components/
│ ├── common/
│ ├── layout/
│ ├── charts/
│ ├── modals/
│
├── pages/
│ ├── admin/
│ ├── user/
│ ├── auth/
│
├── routes/
│ ├── AdminRoutes.jsx
│ ├── UserRoutes.jsx
│
└── styles/


---

## Autenticación

- Autenticación basada en JWT
- El token debe almacenarse de forma segura
- Rutas protegidas:
  - Rutas de administrador requieren rol admin
  - Rutas de usuario requieren sesión activa
- Logout limpia el token y el estado del usuario

---

## Portal de Usuario

### Funcionalidades

- Listado de productos
- Búsqueda por nombre
- Filtros por precio
- Paginación controlada por el backend
- Productos mostrados como cards con imagen, nombre y precio

### Header

- En la esquina derecha:
  - “Bienvenido a Apotheclean, {nombre_usuario}”
- Este elemento es un botón que despliega:
  - Deshabilitar cuenta
  - Logout

### Carrito y Flujo de Venta

1. Login  
   `POST /api/auth/login`

2. Ver productos  
   `GET /api/productos`

3. Crear venta  
   `POST /api/ventas`

4. Completar venta  
   `POST /api/ventas/{uuid}/completar`

- El carrito permite agregar y remover productos
- Las cantidades son visibles y editables
- Soporte para cancelar ventas usando endpoints existentes

---

## Portal de Administrador

### Gestión de Productos

- Ver todos los productos
- Búsqueda por:
  - Nombre
  - Código de barras
- Operaciones CRUD:
  - Crear producto
  - Editar producto
  - Soft delete
- Subida de imagen del producto usando endpoints del backend

---

### Gestión de Ventas

- Registro de ventas físicas
- Listado de ventas en formato de cards
- Al hacer click en una card:
  - Se abre un modal con el detalle completo de la venta

---

### Reportes

#### Ventas por Rango de Fechas

- Filtro por rango de fechas
- Paginación basada en backend

#### Gráfico de Ventas

- Gráfico de tipo pie
- Top 5 productos más vendidos
- Sexta categoría: “Otros” (acumulado del resto)
- Los datos del gráfico deben reflejar exclusivamente la respuesta del backend

---

## Reglas de Integración con la API

- No replicar lógica del backend
- Usar límites, filtros y paginación definidos en la API
- Siempre manejar:
  - Estados de carga
  - Errores
  - Resultados vacíos

---

## Resiliencia y Manejo de Errores

- Cliente HTTP centralizado
- Manejar:
  - Errores de red
  - 401 → redirigir a login
  - 403 → mostrar mensaje de no autorizado
- Retry opcional para fallos transitorios

---

## Manejo de Estado

- Priorizar hooks de React
- Evitar estado global innecesario
- El estado de UI vive en los componentes
- El estado de datos vive en hooks

---

## Reglas de Consistencia de Diseño

- Un solo estilo de botón primario
- Un solo estilo de card
- Modales consistentes en toda la aplicación
- Formularios con layout y validaciones uniformes
- Evitar componentes únicos sin justificación clara

---

## No Objetivos

- No implementar lógica de negocio en el frontend
- No asumir detalles internos del backend o la base de datos
- No aplicar seguridad real en el frontend (solo control visual)

---

## Notas Finales

El frontend debe priorizar:

- Claridad sobre complejidad
- Consistencia sobre experimentación
- Simplicidad sobre abstracción

Ante la duda, reducir complejidad es la decisión correcta.

