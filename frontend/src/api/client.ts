/**
 * Cliente HTTP centralizado para comunicación con el backend.
 * Maneja autenticación JWT, errores y reintentos.
 */

/** URL base de la API */
const API_BASE = '/api';

/** Clave para almacenar el token JWT en localStorage */
const TOKEN_KEY = 'apotheclean_token';

/** Interfaz de respuesta de error de la API */
interface ApiError {
    error: string;
    codigo?: string;
}

/** Excepción personalizada para errores de la API */
export class ApiException extends Error {
    status: number;
    codigo?: string;

    constructor(
        message: string,
        status: number,
        codigo?: string
    ) {
        super(message);
        this.name = 'ApiException';
        this.status = status;
        this.codigo = codigo;
    }
}

/**
 * Obtiene el token JWT almacenado.
 * @returns Token JWT o null si no existe
 */
export function obtenerToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Almacena el token JWT.
 * @param token - Token JWT a almacenar
 */
export function guardarToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Elimina el token JWT almacenado (logout).
 */
export function eliminarToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * Decodifica el payload de un token JWT.
 * @param token - Token JWT a decodificar
 * @returns Payload decodificado o null si es inválido
 */
export function decodificarToken(token: string): Record<string, unknown> | null {
    try {
        const payload = token.split('.')[1];
        const decoded = atob(payload);
        return JSON.parse(decoded);
    } catch {
        return null;
    }
}

/**
 * Verifica si el token JWT ha expirado.
 * @param token - Token JWT a verificar
 * @returns true si el token ha expirado
 */
export function tokenExpirado(token: string): boolean {
    const payload = decodificarToken(token);
    if (!payload || typeof payload.exp !== 'number') return true;

    const ahora = Math.floor(Date.now() / 1000);
    return payload.exp < ahora;
}

/**
 * Construye los headers para las peticiones HTTP.
 * @param incluirAuth - Si incluir el header de autorización
 * @returns Headers configurados
 */
function construirHeaders(incluirAuth: boolean = true): HeadersInit {
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };

    if (incluirAuth) {
        const token = obtenerToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }

    return headers;
}

/**
 * Maneja la respuesta de la API y lanza excepciones en caso de error.
 * @param response - Respuesta fetch
 * @returns Datos JSON de la respuesta
 */
async function manejarRespuesta<T>(response: Response): Promise<T> {
    const data = await response.json();

    if (!response.ok) {
        const error = data as ApiError;

        // Si es 401, limpiar token y redirigir a login
        if (response.status === 401) {
            eliminarToken();
            window.location.href = '/login';
        }

        throw new ApiException(
            error.error || 'Error desconocido',
            response.status,
            error.codigo
        );
    }

    return data as T;
}

/**
 * Realiza una petición GET a la API.
 * @param endpoint - Endpoint de la API (sin /api)
 * @param params - Parámetros de query opcionales
 * @param auth - Si requiere autenticación (default: true)
 * @returns Datos de la respuesta
 */
export async function get<T>(
    endpoint: string,
    params?: Record<string, string | number>,
    auth: boolean = true
): Promise<T> {
    const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            url.searchParams.append(key, String(value));
        });
    }

    const response = await fetch(url.toString(), {
        method: 'GET',
        headers: construirHeaders(auth),
    });

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición POST a la API.
 * @param endpoint - Endpoint de la API (sin /api)
 * @param body - Cuerpo de la petición
 * @param auth - Si requiere autenticación (default: true)
 * @returns Datos de la respuesta
 */
export async function post<T>(
    endpoint: string,
    body: Record<string, unknown>,
    auth: boolean = true
): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: construirHeaders(auth),
        body: JSON.stringify(body),
    });

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición PUT a la API.
 * @param endpoint - Endpoint de la API (sin /api)
 * @param body - Cuerpo de la petición
 * @param auth - Si requiere autenticación (default: true)
 * @returns Datos de la respuesta
 */
export async function put<T>(
    endpoint: string,
    body: Record<string, unknown>,
    auth: boolean = true
): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'PUT',
        headers: construirHeaders(auth),
        body: JSON.stringify(body),
    });

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición DELETE a la API.
 * @param endpoint - Endpoint de la API (sin /api)
 * @param auth - Si requiere autenticación (default: true)
 * @returns Datos de la respuesta
 */
export async function del<T>(
    endpoint: string,
    auth: boolean = true
): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'DELETE',
        headers: construirHeaders(auth),
    });

    return manejarRespuesta<T>(response);
}
