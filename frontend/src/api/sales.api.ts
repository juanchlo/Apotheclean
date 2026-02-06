/**
 * API de ventas y carrito.
 * Funciones para gestionar el carrito (Redis) y las ventas.
 */

import { get, post, del } from './client';

// ==========================================
// TIPOS - Carrito
// ==========================================

/** Item en el carrito */
export interface ItemCarrito {
    producto_id: string;
    nombre: string;
    cantidad: number;
    valor_unitario: string;
    subtotal: string;
    stock_disponible: number;
}

/** Estado del carrito */
export interface Carrito {
    items: ItemCarrito[];
    total_items: number;
    valor_total: string;
}

/** Respuesta del checkout */
export interface CheckoutResponse {
    mensaje: string;
    venta: {
        uuid: string;
        estado: string;
        valor_total: string;
        items: number;
    };
}

// ==========================================
// TIPOS - Ventas
// ==========================================

/** Item de una venta */
export interface ItemVenta {
    producto_id: string;
    cantidad: number;
    precio_unitario: string;
    subtotal: string;
}

/** Estructura de una venta completa */
export interface Venta {
    uuid: string;
    fecha: string;
    modalidad: string;
    estado: string;
    valor_total_cop: string;
    items: ItemVenta[];
    comprador_id?: string;
    vendedor_id: string;
}

/** Parámetros para filtrar el reporte de ventas */
export interface ReporteVentasParams {
    fecha_inicio?: string;
    fecha_fin?: string;
    modalidad?: string;
    estado?: string;
    limite?: number;
    offset?: number;
}

/** Respuesta del reporte de ventas */
export interface ReporteVentasResponse {
    ventas: Venta[];
    total: number;
    limite: number;
    offset: number;
}

// ==========================================
// FUNCIONES - Carrito (Redis)
// ==========================================

/**
 * Obtiene el carrito actual del usuario.
 * El carrito se almacena temporalmente en Redis.
 * @returns Estado actual del carrito
 */
export async function obtenerCarrito(): Promise<Carrito> {
    return get<Carrito>('/carrito');
}

/**
 * Agrega un producto al carrito (Redis).
 * @param productoId - UUID del producto
 * @param cantidad - Cantidad a agregar
 */
export async function agregarAlCarrito(
    productoId: string,
    cantidad: number = 1
): Promise<void> {
    await post('/carrito/items', {
        producto_id: productoId,
        cantidad
    });
}

/**
 * Elimina o reduce cantidad de un producto del carrito.
 * @param productoId - UUID del producto
 * @param cantidad - Cantidad a reducir (opcional, si no se indica elimina todo)
 */
export async function eliminarDelCarrito(
    productoId: string,
    cantidad?: number
): Promise<void> {
    const url = cantidad
        ? `/carrito/items/${productoId}?cantidad=${cantidad}`
        : `/carrito/items/${productoId}`;
    await del(url);
}

/**
 * Vacía completamente el carrito (elimina key de Redis).
 */
export async function vaciarCarrito(): Promise<void> {
    await del('/carrito');
}

/**
 * Convierte el carrito en una venta pendiente.
 * Los datos se toman de Redis y se crea la venta en BD.
 * @param modalidad - 'virtual' o 'fisica'
 * @returns Datos de la venta creada
 */
export async function checkoutCarrito(
    modalidad: 'virtual' | 'fisica' = 'fisica'
): Promise<CheckoutResponse> {
    return post<CheckoutResponse>('/carrito/checkout', { modalidad });
}

// ==========================================
// FUNCIONES - Ventas
// ==========================================

/**
 * Completa una venta pendiente (descuenta stock).
 * @param uuid - UUID de la venta
 * @returns Venta completada
 */
export async function completarVenta(uuid: string): Promise<Venta> {
    return post<Venta>(`/ventas/${uuid}/completar`, {});
}

/**
 * Cancela una venta pendiente.
 * @param uuid - UUID de la venta
 */
export async function cancelarVenta(uuid: string): Promise<void> {
    await post(`/ventas/${uuid}/cancelar`, {});
}

/**
 * Obtiene el reporte de ventas con filtros.
 * @param params - Filtros de fecha, modalidad, estado y paginación
 * @returns Reporte de ventas detallado
 */
export async function obtenerReporteVentas(
    params: ReporteVentasParams
): Promise<ReporteVentasResponse> {
    const queryParams: Record<string, string | number> = {};

    if (params.fecha_inicio) queryParams.fecha_inicio = params.fecha_inicio;
    if (params.fecha_fin) queryParams.fecha_fin = params.fecha_fin;
    if (params.modalidad) queryParams.modalidad = params.modalidad;
    if (params.estado) queryParams.estado = params.estado;
    if (params.limite) queryParams.limite = params.limite;
    if (params.offset !== undefined) queryParams.offset = params.offset;

    return get<ReporteVentasResponse>('/ventas/reporte', queryParams);
}
