/**
 * Página de Gestión de Ventas para Administrador.
 * Permite buscar productos, agregarlos al carrito y confirmar ventas.
 */

import { useState, useEffect } from 'react';

import { listarProductos, obtenerUrlImagenProducto } from '../../api/products.api';
import type { Producto } from '../../api/products.api';
import {
    obtenerCarrito,
    agregarAlCarrito,
    eliminarDelCarrito,
    vaciarCarrito,
    checkoutCarrito,
    completarVenta
} from '../../api/sales.api';
import type { Carrito, ItemCarrito } from '../../api/sales.api';
import { ApiException } from '../../api/client';
import { AdminNavbar } from '../../components/layout/AdminNavbar';
import './Sales.css';

/**
 * Componente de página de ventas.
 * Incluye búsqueda de productos, carrito y checkout.
 */
export function Sales() {
    // Estado de productos
    const [productos, setProductos] = useState<Producto[]>([]);
    const [busqueda, setBusqueda] = useState('');

    // Estado del carrito (Redis)
    const [carrito, setCarrito] = useState<Carrito | null>(null);

    // Estados UI
    const [cargando, setCargando] = useState(false);
    const [cargandoCarrito, setCargandoCarrito] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [exito, setExito] = useState<string | null>(null);
    const [procesandoVenta, setProcesandoVenta] = useState(false);

    // Cargar productos al montar
    useEffect(() => {
        cargarProductos();
        cargarCarrito();
    }, []);

    /**
     * Carga la lista de productos activos.
     */
    const cargarProductos = async () => {
        setCargando(true);
        try {
            const respuesta = await listarProductos(1000, 0, false);
            setProductos(respuesta.productos);
        } catch (err) {
            console.error('Error al cargar productos:', err);
            setError('Error al cargar productos');
        } finally {
            setCargando(false);
        }
    };

    /**
     * Carga el carrito desde Redis.
     */
    const cargarCarrito = async () => {
        setCargandoCarrito(true);
        try {
            const carritoActual = await obtenerCarrito();
            setCarrito(carritoActual);
        } catch (err) {
            console.error('Error al cargar carrito:', err);
            setCarrito({ items: [], total_items: 0, valor_total: '0' });
        } finally {
            setCargandoCarrito(false);
        }
    };

    /**
     * Agrega un producto al carrito.
     */
    const handleAgregarProducto = async (producto: Producto) => {
        setError(null);
        try {
            await agregarAlCarrito(producto.uuid, 1);
            await cargarCarrito();
            mostrarExito(`${producto.nombre} agregado al carrito`);
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Error al agregar producto');
            }
        }
    };

    /**
     * Incrementa la cantidad de un item en el carrito.
     */
    const handleIncrementar = async (item: ItemCarrito) => {
        try {
            await agregarAlCarrito(item.producto_id, 1);
            await cargarCarrito();
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            }
        }
    };

    /**
     * Decrementa la cantidad de un item en el carrito.
     */
    const handleDecrementar = async (item: ItemCarrito) => {
        try {
            if (item.cantidad <= 1) {
                await eliminarDelCarrito(item.producto_id);
            } else {
                await eliminarDelCarrito(item.producto_id, 1);
            }
            await cargarCarrito();
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            }
        }
    };

    /**
     * Elimina un item completamente del carrito.
     */
    const handleEliminarItem = async (item: ItemCarrito) => {
        try {
            await eliminarDelCarrito(item.producto_id);
            await cargarCarrito();
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            }
        }
    };

    /**
     * Vacía el carrito completamente.
     */
    const handleVaciarCarrito = async () => {
        if (!carrito || carrito.items.length === 0) return;

        try {
            await vaciarCarrito();
            await cargarCarrito();
            mostrarExito('Carrito vaciado');
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            }
        }
    };

    /**
     * Confirma la venta: checkout + completar.
     */
    const handleConfirmarVenta = async () => {
        if (!carrito || carrito.items.length === 0) return;

        setProcesandoVenta(true);
        setError(null);

        try {
            // 1. Checkout: crea venta pendiente desde Redis
            const checkoutResp = await checkoutCarrito('fisica');

            // 2. Completar: descuenta stock y marca como completada
            await completarVenta(checkoutResp.venta.uuid);

            // 3. Recargar carrito (debería estar vacío)
            await cargarCarrito();

            // 4. Recargar productos para actualizar stock
            await cargarProductos();

            mostrarExito(`¡Venta completada! Total: ${formatearMoneda(checkoutResp.venta.valor_total)}`);
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Error al procesar la venta');
            }
        } finally {
            setProcesandoVenta(false);
        }
    };

    /**
     * Muestra mensaje de éxito temporal.
     */
    const mostrarExito = (mensaje: string) => {
        setExito(mensaje);
        setTimeout(() => setExito(null), 3000);
    };

    /**
     * Formatea un valor en COP.
     */
    const formatearMoneda = (valor: string | number): string => {
        const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(numero);
    };

    // Filtrar productos por búsqueda
    const productosFiltrados = productos.filter(p =>
        p.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        p.barcode.includes(busqueda)
    );

    return (
        <div className="sales-page">
            {/* Header */}
            {/* Header */}
            <AdminNavbar />

            {/* Contenido principal */}
            <main className="sales-main">
                <div className="sales-container">
                    {/* Título */}
                    <div className="sales-title-section">
                        <div>
                            <h1>Registro de Ventas</h1>
                            <p>Busca productos y agrégalos al carrito para registrar una venta</p>
                        </div>
                    </div>

                    {/* Mensajes */}
                    {error && (
                        <div className="alert alert-error">
                            {error}
                            <button onClick={() => setError(null)} className="alert-close">×</button>
                        </div>
                    )}

                    {exito && (
                        <div className="alert alert-success">
                            {exito}
                        </div>
                    )}

                    <div className="sales-layout">
                        {/* Panel de productos */}
                        <div className="sales-products-panel">
                            <div className="sales-products-header">
                                <h2>Productos</h2>
                                <div className="sales-search">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="11" cy="11" r="8" />
                                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                    </svg>
                                    <input
                                        type="text"
                                        className="input"
                                        placeholder="Buscar por nombre o código..."
                                        value={busqueda}
                                        onChange={(e) => setBusqueda(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="sales-products-list">
                                {cargando ? (
                                    <div className="sales-loading">
                                        <span className="loading-spinner" />
                                        Cargando productos...
                                    </div>
                                ) : productosFiltrados.length === 0 ? (
                                    <div className="sales-empty">
                                        <p>No se encontraron productos</p>
                                    </div>
                                ) : (
                                    productosFiltrados.map((producto) => (
                                        <div
                                            key={producto.uuid}
                                            className={`sales-product-item ${producto.stock <= 0 ? 'out-of-stock' : ''}`}
                                            onClick={() => producto.stock > 0 && handleAgregarProducto(producto)}
                                        >
                                            <div className="sales-product-image">
                                                {producto.imagen_uuid ? (
                                                    <img
                                                        src={obtenerUrlImagenProducto(producto.uuid)}
                                                        alt={producto.nombre}
                                                        onError={(e) => {
                                                            (e.target as HTMLImageElement).style.display = 'none';
                                                        }}
                                                    />
                                                ) : (
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                                        <circle cx="8.5" cy="8.5" r="1.5" />
                                                        <polyline points="21 15 16 10 5 21" />
                                                    </svg>
                                                )}
                                            </div>
                                            <div className="sales-product-info">
                                                <span className="sales-product-name">{producto.nombre}</span>
                                                <span className="sales-product-barcode">{producto.barcode}</span>
                                            </div>
                                            <div className="sales-product-meta">
                                                <span className="sales-product-price">
                                                    {formatearMoneda(producto.valor_unitario)}
                                                </span>
                                                <span className={`sales-product-stock ${producto.stock <= 5 ? 'low' : ''}`}>
                                                    {producto.stock} unid.
                                                </span>
                                            </div>
                                            {producto.stock > 0 && (
                                                <div className="sales-product-add">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <line x1="12" y1="5" x2="12" y2="19" />
                                                        <line x1="5" y1="12" x2="19" y2="12" />
                                                    </svg>
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Panel del carrito */}
                        <div className="sales-cart-panel">
                            <div className="sales-cart-header">
                                <h2>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="9" cy="21" r="1" />
                                        <circle cx="20" cy="21" r="1" />
                                        <path d="m1 1 4 1 2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                                    </svg>
                                    Carrito
                                </h2>
                                {carrito && carrito.items.length > 0 && (
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={handleVaciarCarrito}
                                    >
                                        Vaciar
                                    </button>
                                )}
                            </div>

                            <div className="sales-cart-items">
                                {cargandoCarrito ? (
                                    <div className="sales-loading">
                                        <span className="loading-spinner" />
                                    </div>
                                ) : !carrito || carrito.items.length === 0 ? (
                                    <div className="sales-cart-empty">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <circle cx="9" cy="21" r="1" />
                                            <circle cx="20" cy="21" r="1" />
                                            <path d="m1 1 4 1 2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                                        </svg>
                                        <p>El carrito está vacío</p>
                                        <span>Haz clic en un producto para agregarlo</span>
                                    </div>
                                ) : (
                                    carrito.items.map((item) => (
                                        <div key={item.producto_id} className="sales-cart-item">
                                            <div className="sales-cart-item-info">
                                                <span className="sales-cart-item-name">{item.nombre}</span>
                                                <span className="sales-cart-item-price">
                                                    {formatearMoneda(item.valor_unitario)} c/u
                                                </span>
                                            </div>
                                            <div className="sales-cart-item-controls">
                                                <button
                                                    className="sales-cart-btn"
                                                    onClick={() => handleDecrementar(item)}
                                                >
                                                    −
                                                </button>
                                                <span className="sales-cart-item-qty">{item.cantidad}</span>
                                                <button
                                                    className="sales-cart-btn"
                                                    onClick={() => handleIncrementar(item)}
                                                    disabled={item.cantidad >= item.stock_disponible}
                                                >
                                                    +
                                                </button>
                                            </div>
                                            <div className="sales-cart-item-subtotal">
                                                {formatearMoneda(item.subtotal)}
                                            </div>
                                            <button
                                                className="sales-cart-item-remove"
                                                onClick={() => handleEliminarItem(item)}
                                            >
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <line x1="18" y1="6" x2="6" y2="18" />
                                                    <line x1="6" y1="6" x2="18" y2="18" />
                                                </svg>
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>

                            {/* Footer del carrito */}
                            {carrito && carrito.items.length > 0 && (
                                <div className="sales-cart-footer">
                                    <div className="sales-cart-total">
                                        <span>Total ({carrito.total_items} items)</span>
                                        <strong>{formatearMoneda(carrito.valor_total)}</strong>
                                    </div>
                                    <button
                                        className="btn btn-primary btn-block"
                                        onClick={handleConfirmarVenta}
                                        disabled={procesandoVenta}
                                    >
                                        {procesandoVenta ? (
                                            <>
                                                <span className="loading-spinner" />
                                                Procesando...
                                            </>
                                        ) : (
                                            <>
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <polyline points="20 6 9 17 4 12" />
                                                </svg>
                                                Confirmar Venta
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
