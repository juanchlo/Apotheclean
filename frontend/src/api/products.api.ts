/**
 * API de productos.
 * Funciones CRUD para gestionar productos.
 */

import { get, post, put, del, obtenerToken } from './client';

/** Datos de un producto */
export interface Producto {
    uuid: string;
    nombre: string;
    barcode: string;
    valor_unitario: string;
    stock: number;
    descripcion: string | null;
    imagen_uuid: string | null;
}

/** Respuesta de listar productos */
export interface ListarProductosResponse {
    productos: Producto[];
    total: number;
    limite: number;
    offset: number;
}

/** Datos para crear un producto */
export interface CrearProductoInput {
    [key: string]: string | number | undefined;
    nombre: string;
    barcode: string;
    valor_unitario: number;
    stock: number;
    descripcion?: string;
}

/** Datos para actualizar un producto */
export interface ActualizarProductoInput {
    [key: string]: string | number | undefined;
    nombre?: string;
    valor_unitario?: number;
    stock?: number;
    descripcion?: string;
}

/** Caché de productos para evitar múltiples llamadas */
const productosCache = new Map<string, Producto>();

/**
 * Lista todos los productos con paginación.
 * @param limite - Número máximo de resultados
 * @param offset - Número de resultados a saltar
 * @param incluirEliminados - Si incluir productos eliminados
 * @returns Lista de productos
 */
export async function listarProductos(
    limite: number = 100,
    offset: number = 0,
    incluirEliminados: boolean = false
): Promise<ListarProductosResponse> {
    const params: Record<string, string | number> = { limite, offset };
    if (incluirEliminados) {
        params.incluir_eliminados = 'true';
    }
    return get<ListarProductosResponse>('/productos', params);
}

/**
 * Obtiene un producto por su UUID.
 * Utiliza caché para evitar llamadas repetidas.
 * @param uuid - UUID del producto
 * @returns Datos del producto
 */
export async function obtenerProducto(uuid: string): Promise<Producto> {
    // Verificar si está en caché
    if (productosCache.has(uuid)) {
        return productosCache.get(uuid)!;
    }

    const producto = await get<Producto>(`/productos/${uuid}`);
    productosCache.set(uuid, producto);
    return producto;
}

/**
 * Obtiene múltiples productos y los cachea.
 * @param uuids - Lista de UUIDs de productos
 * @returns Mapa de UUID a Producto
 */
export async function obtenerProductosBatch(uuids: string[]): Promise<Map<string, Producto>> {
    const resultado = new Map<string, Producto>();
    const faltantes: string[] = [];

    // Verificar cuáles ya están en caché
    for (const uuid of uuids) {
        if (productosCache.has(uuid)) {
            resultado.set(uuid, productosCache.get(uuid)!);
        } else {
            faltantes.push(uuid);
        }
    }

    // Obtener los faltantes en paralelo
    if (faltantes.length > 0) {
        const promesas = faltantes.map(uuid =>
            obtenerProducto(uuid)
                .then(producto => {
                    resultado.set(uuid, producto);
                })
                .catch(() => {
                    // Si falla, poner un placeholder
                    resultado.set(uuid, {
                        uuid,
                        nombre: 'Producto no disponible',
                        barcode: '---',
                        valor_unitario: '0',
                        stock: 0,
                        descripcion: null,
                        imagen_uuid: null
                    });
                })
        );

        await Promise.all(promesas);
    }

    return resultado;
}

/**
 * Crea un nuevo producto.
 * @param datos - Datos del producto a crear
 * @returns Producto creado
 */
export async function crearProducto(datos: CrearProductoInput): Promise<Producto> {
    const producto = await post<Producto>('/productos', datos);
    productosCache.set(producto.uuid, producto);
    return producto;
}

/**
 * Actualiza un producto existente.
 * @param uuid - UUID del producto
 * @param datos - Datos a actualizar
 * @returns Producto actualizado
 */
export async function actualizarProducto(
    uuid: string,
    datos: ActualizarProductoInput
): Promise<Producto> {
    const producto = await put<Producto>(`/productos/${uuid}`, datos);
    productosCache.set(uuid, producto);
    return producto;
}

/**
 * Elimina un producto (soft delete).
 * @param uuid - UUID del producto
 */
export async function eliminarProducto(uuid: string): Promise<void> {
    await del(`/productos/${uuid}`);
    productosCache.delete(uuid);
}

/**
 * Restaura un producto eliminado (revierte soft delete).
 * @param uuid - UUID del producto d
 * @returns Producto restaurado
 */
export async function restaurarProducto(uuid: string): Promise<Producto> {
    const producto = await post<Producto>(`/productos/${uuid}/restaurar`, {});
    productosCache.set(uuid, producto);
    return producto;
}

/**
 * Sube la imagen de un producto.
 * @param uuid - UUID del producto
 * @param imagen - Archivo de imagen
 * @returns Producto actualizado
 */
export async function subirImagenProducto(
    uuid: string,
    imagen: File
): Promise<Producto> {
    const formData = new FormData();
    formData.append('imagen', imagen);

    const token = obtenerToken();
    const response = await fetch(`/api/productos/${uuid}/imagen`, {
        method: 'POST',
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Error al subir imagen');
    }

    const producto = await response.json();
    productosCache.set(uuid, producto);
    return producto;
}

/**
 * Obtiene la URL de la imagen de un producto.
 * @param uuid - UUID del producto
 * @returns URL de la imagen
 */
export function obtenerUrlImagenProducto(uuid: string): string {
    return `/api/productos/${uuid}/imagen`;
}

/**
 * Limpia la caché de productos.
 */
export function limpiarCacheProductos(): void {
    productosCache.clear();
}

/**
 * Invalida un producto específico del caché.
 * @param uuid - UUID del producto a invalidar
 */
export function invalidarProductoCache(uuid: string): void {
    productosCache.delete(uuid);
}
