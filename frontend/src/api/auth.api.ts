/**
 * API de autenticación.
 * Funciones para login, registro y gestión de sesión.
 */

import { post, guardarToken, eliminarToken, obtenerToken, decodificarToken, tokenExpirado } from './client';

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
    token: string;
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

    // Guardar token
    guardarToken(respuesta.token);

    // Decodificar y retornar datos del usuario
    const payload = decodificarToken(respuesta.token);
    if (!payload) {
        throw new Error('Token inválido recibido del servidor');
    }

    return {
        uuid: payload.sub as string,
        username: payload.username as string,
        email: payload.email as string,
        nombre: payload.nombre as string,
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
 */
export function logout(): void {
    eliminarToken();
}

/**
 * Obtiene el usuario actual desde el token almacenado.
 * @returns Usuario actual o null si no hay sesión válida
 */
export function obtenerUsuarioActual(): Usuario | null {
    const token = obtenerToken();
    if (!token || tokenExpirado(token)) {
        eliminarToken();
        return null;
    }

    const payload = decodificarToken(token);
    if (!payload) return null;

    return {
        uuid: payload.sub as string,
        username: payload.username as string,
        email: payload.email as string,
        nombre: payload.nombre as string,
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
