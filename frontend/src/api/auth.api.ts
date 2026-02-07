/**
 * API de autenticación.
 * Funciones para login, registro y gestión de sesión.
 */

import { post, guardarToken, eliminarToken, obtenerToken, decodificarToken, tokenExpirado, obtenerRefreshToken } from './client';

/** Datos del usuario autenticado */
export interface Usuario {
    uuid: string;
    username: string;
    email: string;
    nombre: string;
    rol: 'admin' | 'cliente';
}

/** Respuesta del endpoint de login */
interface LoginResponse {
    mensaje: string;
    access_token: string;
    refresh_token: string;
}

/** Respuesta del endpoint de registro */
interface RegistroResponse {
    mensaje: string;
    username: string;
}



/**
 * Inicia sesión con las credenciales proporcionadas.
 * @param credenciales - Username o email con password
 * @returns Usuario autenticado
 */
export async function login(credenciales: {
    username?: string;
    email?: string;
    password: string;
}): Promise<Usuario> {
    const respuesta = await post<LoginResponse>('/auth/login', credenciales, false);

    // Guardar tokens
    guardarToken(respuesta.access_token, respuesta.refresh_token);

    // Decodificar y retornar datos del usuario (usando access token)
    const payload = decodificarToken(respuesta.access_token);
    if (!payload) {
        throw new Error('Token inválido recibido del servidor');
    }

    return {
        uuid: payload.sub as string,
        username: payload.username as string || 'Usuario', // Failsafe
        email: payload.email as string || '',
        nombre: payload.nombre as string || '',
        rol: payload.rol as 'admin' | 'cliente',
    };
}

/**
 * Registra un nuevo usuario cliente.
 * @param datos - Datos del usuario a registrar
 * @returns Mensaje de éxito y username
 */
export async function registro(datos: {
    username: string;
    password: string;
    email: string;
    nombre: string;
}): Promise<RegistroResponse> {
    return post<RegistroResponse>('/auth/registro', datos, false);
}

/**
 * Cierra la sesión del usuario actual.
 * Intenta revocar el refresh token en backend.
 */
export async function logout(): Promise<void> {
    const refreshToken = obtenerRefreshToken();
    if (refreshToken) {
        try {
            // Intentar avisar al backend (blacklist)
            // No esperamos respuesta, es "fire and forget" desde perspectiva de UX
            await post('/auth/logout', { refresh_token: refreshToken }, false);
        } catch (error) {
            console.warn('Error al notificar logout al backend:', error);
        }
    }
    eliminarToken();
}

/**
 * Obtiene el usuario actual desde el token almacenado.
 * @returns Usuario actual o null si no hay sesión válida
 */
export function obtenerUsuarioActual(): Usuario | null {
    const token = obtenerToken();
    // Nota: Ahora permitimos tokens expirados localmente si tenemos refresh token,
    // pero para "obtenerUsuarioActual", generalmente queremos saber si hay sesión.
    // Si el access token expiró, el interceptor lo renovará en la próxima petición.
    // Aquí solo decodificamos lo que hay.
    if (!token) {
        return null;
    }

    // Si está expirado pero hay refresh token, podríamos asumir que "sigue logueado".
    // Pero si decodificar falla, es null.
    const payload = decodificarToken(token);
    if (!payload) return null;

    // Si está expirado y NO hay refresh token, entonces sí es inválido.
    // Si hay refresh token, permitimos retornar el usuario para que la app intente
    // hacer peticiones y el interceptor se encargue de renovar.
    if (tokenExpirado(token) && !obtenerRefreshToken()) {
        return null;
    }

    return {
        uuid: payload.sub as string,
        username: payload.username as string || 'Usuario', // El payload nuevo es reducido, ojo
        email: payload.email as string || '',
        nombre: payload.nombre as string || '',
        rol: payload.rol as 'admin' | 'cliente',
    };
}

/**
 * Verifica si hay una sesión activa válida.
 * @returns true si hay una sesión válida
 */
export function estaAutenticado(): boolean {
    return obtenerUsuarioActual() !== null;
}

/**
 * Verifica si el usuario actual es administrador.
 * @returns true si el usuario es admin
 */
export function esAdmin(): boolean {
    const usuario = obtenerUsuarioActual();
    return usuario?.rol === 'admin';
}
