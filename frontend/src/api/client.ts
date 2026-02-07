/**
 * Cliente HTTP centralizado para comunicación con el backend.
 * Maneja autenticación JWT, errores, reintentos y renovación de tokens.
 */

/** URL base de la API */
const API_BASE = '/api';

/** Clave para almacenar el token JWT en localStorage */
const TOKEN_KEY = 'apotheclean_token';
/** Clave para almacenar el refresh token en localStorage */
const REFRESH_TOKEN_KEY = 'apotheclean_refresh_token';

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
 * Obtiene el token JWT (Access Token) almacenado.
 * @returns Token JWT o null si no existe
 */
export function obtenerToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Obtiene el Refresh Token almacenado.
 * @returns Refresh Token o null si no existe
 */
export function obtenerRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Almacena los tokens JWT.
 * @param accessToken - Token de acceso
 * @param refreshToken - Token de refresco (opcional)
 */
export function guardarToken(accessToken: string, refreshToken?: string): void {
    localStorage.setItem(TOKEN_KEY, accessToken);
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
}

/**
 * Elimina los tokens almacenados (logout local).
 */
export function eliminarToken(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
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
    const headers: Record<string, string> = {
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
 * Intenta renovar el access token usando el refresh token.
 * @returns Nuevo access token o null si falla.
 */
async function renovarToken(): Promise<string | null> {
    const refreshToken = obtenerRefreshToken();
    if (!refreshToken) return null;

    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (response.ok) {
            const data = await response.json();
            // Guardar nuevos tokens (access + refresh rotado)
            guardarToken(data.access_token, data.refresh_token);
            return data.access_token;
        } else {
            // Si el refresh falla (expirado, revocado), limpiamos todo
            eliminarToken();
            return null;
        }
    } catch (error) {
        console.error("Error renovando token:", error);
        return null;
    }
}

/**
 * Wrapper sobre fetch para manejar intercepción de 401 y renovación de tokens.
 */
async function fetchConInterceptor(
    url: string,
    options: RequestInit,
    requiereAuth: boolean = true
): Promise<Response> {
    // 1. Primer intento
    let response = await fetch(url, options);

    // 2. Si es 401 y requiere auth, intentar refresh
    if (response.status === 401 && requiereAuth) {
        const nuevoToken = await renovarToken();

        if (nuevoToken) {
            // Reintentar con nuevo token
            const nuevosHeaders = construirHeaders(true);
            const nuevasOpciones = {
                ...options,
                headers: nuevosHeaders
            };
            response = await fetch(url, nuevasOpciones);
        } else {
            // Si no se pudo renovar, redirigir a login
            eliminarToken();
            window.location.href = '/login';
        }
    }

    return response;
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

    const response = await fetchConInterceptor(url.toString(), {
        method: 'GET',
        headers: construirHeaders(auth),
    }, auth);

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición POST a la API.
 */
export async function post<T>(
    endpoint: string,
    body: Record<string, unknown>,
    auth: boolean = true
): Promise<T> {
    const response = await fetchConInterceptor(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: construirHeaders(auth),
        body: JSON.stringify(body),
    }, auth);

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición PUT a la API.
 */
export async function put<T>(
    endpoint: string,
    body: Record<string, unknown>,
    auth: boolean = true
): Promise<T> {
    const response = await fetchConInterceptor(`${API_BASE}${endpoint}`, {
        method: 'PUT',
        headers: construirHeaders(auth),
        body: JSON.stringify(body),
    }, auth);

    return manejarRespuesta<T>(response);
}

/**
 * Realiza una petición DELETE a la API.
 */
export async function del<T>(
    endpoint: string,
    auth: boolean = true
): Promise<T> {
    const response = await fetchConInterceptor(`${API_BASE}${endpoint}`, {
        method: 'DELETE',
        headers: construirHeaders(auth),
    }, auth);

    return manejarRespuesta<T>(response);
}
