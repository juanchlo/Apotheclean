/**
 * API de ventas.
 * Funciones para gestionar y reportar ventas.
 */

import { get, post } from './client';

/** Item de una venta */
export interface ItemVenta {
    producto_id: string; // Changed from producto_uuid to match backend
    cantidad: number;
    precio_unitario: string;
    subtotal: string;
}

/** Estructura de una venta completa */
export interface Venta {
    uuid: string;
    fecha: string;
    valor_total_cop: string; // Changed from total: number to match backend string decimal
    modalidad: 'virtual' | 'fisica'; // Added
    estado: 'pendiente' | 'completada' | 'cancelada'; // Added
    items: ItemVenta[];
    comprador_uuid?: string;
    vendedor_uuid: string;
}

/** Parámetros para filtrar el reporte de ventas */
export interface ReporteVentasParams {
    fecha_inicio?: string;
    fecha_fin?: string;
    limite?: number;
    offset?: number;
    modalidad?: 'virtual' | 'fisica' | ''; // Added
    estado?: 'pendiente' | 'completada' | 'cancelada' | ''; // Added
}

/** Respuesta del reporte de ventas */
export interface ReporteVentasResponse {
    ventas: Venta[];
    total: number;
    resumen: {
        total_ventas: number;
        total_items: number;
        ingresos_totales: number;
    };
}

/**
 * Obtiene el reporte de ventas con filtros.
 * @param params - Filtros de fecha y paginación
 * @returns Reporte de ventas detallado
 */
export async function obtenerReporteVentas(
    params: ReporteVentasParams
): Promise<ReporteVentasResponse> {
    const queryParams: Record<string, string | number> = {};

    if (params.fecha_inicio) queryParams.fecha_inicio = params.fecha_inicio;
    if (params.fecha_fin) queryParams.fecha_fin = params.fecha_fin;
    if (params.limite) queryParams.limite = params.limite;
    if (params.offset) queryParams.offset = params.offset;
    if (params.modalidad) queryParams.modalidad = params.modalidad;
    if (params.estado) queryParams.estado = params.estado;

    return get<ReporteVentasResponse>('/ventas/reporte', queryParams);
}

/**
 * Registra una nueva venta.
 * @param items - Lista de items a vender
 * @returns Venta creada
 */
export async function registrarVenta(items: { producto_id: string; cantidad: number }[]): Promise<Venta> {
    return post<Venta>('/ventas', { items });
}
