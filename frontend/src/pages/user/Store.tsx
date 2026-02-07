/**
 * Página de Tienda para Usuarios (Clientes).
 * Permite buscar productos, agregarlos al carrito y realizar compras.
 */

import { useState, useEffect } from 'react';

import { listarProductos } from '../../api/products.api';
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
import { UserNavbar } from '../../components/layout/UserNavbar';
import { ProductCard } from '../../components/common/ProductCard';
import './Store.css';

/**
 * Componente de página de tienda.
 * Incluye búsqueda de productos, carrito y checkout.
 */
export function Store() {
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
    const [procesandoCompra, setProcesandoCompra] = useState(false);

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
     * Valida que no se exceda el stock disponible.
     */
    const handleAgregarProducto = async (producto: Producto) => {
        setError(null);

        // Verificar si el producto ya está en el carrito
        const itemEnCarrito = carrito?.items.find(item => item.producto_id === producto.uuid);

        // Validar stock disponible
        if (itemEnCarrito) {
            // Si ya está en el carrito, verificar que no se exceda el stock
            if (itemEnCarrito.cantidad >= producto.stock) {
                setError(`No puedes agregar más unidades. Stock disponible: ${producto.stock}`);
                return;
            }
        } else {
            // Si no está en el carrito, verificar que haya stock
            if (producto.stock <= 0) {
                setError(`Producto sin stock disponible`);
                return;
            }
        }

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
     * Verifica si se puede agregar más cantidad de un producto al carrito.
     */
    const puedeAgregarMas = (producto: Producto): boolean => {
        const itemEnCarrito = carrito?.items.find(item => item.producto_id === producto.uuid);

        if (!itemEnCarrito) {
            // Si no está en el carrito, solo verificar que haya stock
            return producto.stock > 0;
        }

        // Si está en el carrito, verificar que la cantidad no exceda el stock
        return itemEnCarrito.cantidad < producto.stock;
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
     * Confirma la compra: checkout + completar.
     * Utiliza modalidad 'virtual' por defecto para clientes.
     */
    const handleConfirmarCompra = async () => {
        if (!carrito || carrito.items.length === 0) return;

        setProcesandoCompra(true);
        setError(null);

        try {
            // 1. Checkout: crea venta pendiente desde Redis (modalidad virtual)
            const checkoutResp = await checkoutCarrito('virtual');

            // 2. Completar: descuenta stock y marca como completada
            // NOTA: En un flujo real esto podría ser después de una pasarela de pago.
            // Aquí simulamos el pago exitoso inmediato.
            await completarVenta(checkoutResp.venta.uuid);

            // 3. Recargar carrito (debería estar vacío)
            await cargarCarrito();

            // 4. Recargar productos para actualizar stock
            await cargarProductos();

            mostrarExito(`¡Compra exitosa! Total: ${formatearMoneda(checkoutResp.venta.valor_total)}`);
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Error al procesar la compra');
            }
        } finally {
            setProcesandoCompra(false);
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
        <div className="store-page">
            {/* Header de Usuario */}
            <UserNavbar />

            {/* Contenido principal */}
            <main className="store-main">
                <div className="store-container">
                    {/* Título */}
                    <div className="store-title-section">
                        <h1>Catálogo de Productos</h1>
                        <p>Explora nuestra farmacia y recibe tus pedidos a domicilio</p>
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

                    <div className="store-layout">
                        {/* Panel de productos */}
                        <div className="store-products-panel">
                            <div className="store-products-header">
                                <h2>Productos Disponibles</h2>
                                <div className="store-search">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="11" cy="11" r="8" />
                                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                    </svg>
                                    <input
                                        type="text"
                                        className="input"
                                        placeholder="Buscar producto por nombre..."
                                        value={busqueda}
                                        onChange={(e) => setBusqueda(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="store-products-list">
                                {cargando ? (
                                    <div className="store-loading">
                                        <span className="loading-spinner" />
                                        Cargando productos...
                                    </div>
                                ) : productosFiltrados.length === 0 ? (
                                    <div className="store-empty">
                                        <p>No se encontraron productos</p>
                                    </div>
                                ) : (
                                    productosFiltrados.map((producto) => {
                                        const puedeAgregar = puedeAgregarMas(producto);
                                        return (
                                            <ProductCard
                                                key={producto.uuid}
                                                producto={producto}
                                                onClick={() => puedeAgregar && handleAgregarProducto(producto)}
                                                variant={!puedeAgregar ? 'no-hover' : 'default'}
                                                className={!puedeAgregar ? 'out-of-stock' : ''}
                                                actions={puedeAgregar && (
                                                    <button
                                                        className="store-product-add-btn"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleAgregarProducto(producto);
                                                        }}
                                                        title="Agregar al carrito"
                                                    >
                                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                                                            <line x1="3" y1="6" x2="21" y2="6" />
                                                            <path d="M16 10a4 4 0 0 1-8 0" />
                                                        </svg>
                                                    </button>
                                                )}
                                            />
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        {/* Panel del carrito */}
                        <div className="store-cart-panel">
                            <div className="store-cart-header">
                                <h2>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="9" cy="21" r="1" />
                                        <circle cx="20" cy="21" r="1" />
                                        <path d="m1 1 4 1 2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                                    </svg>
                                    Mi Carrito
                                </h2>
                                {carrito && carrito.items.length > 0 && (
                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleVaciarCarrito}
                                    >
                                        Vaciar
                                    </button>
                                )}
                            </div>

                            <div className="store-cart-items">
                                {cargandoCarrito ? (
                                    <div className="store-loading">
                                        <span className="loading-spinner" />
                                    </div>
                                ) : !carrito || carrito.items.length === 0 ? (
                                    <div className="store-cart-empty">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <circle cx="9" cy="21" r="1" />
                                            <circle cx="20" cy="21" r="1" />
                                            <path d="m1 1 4 1 2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                                        </svg>
                                        <p>Tu carrito está vacío</p>
                                        <span>Explora el catálogo para agregar productos</span>
                                    </div>
                                ) : (
                                    carrito.items.map((item) => (
                                        <div key={item.producto_id} className="store-cart-item">
                                            <div className="store-cart-item-info">
                                                <span className="store-cart-item-name">{item.nombre}</span>
                                                <span className="store-cart-item-price">
                                                    {formatearMoneda(item.valor_unitario)}
                                                </span>
                                            </div>
                                            <div className="store-cart-item-controls">
                                                <button
                                                    className="store-cart-btn"
                                                    onClick={() => handleDecrementar(item)}
                                                >
                                                    −
                                                </button>
                                                <span className="store-cart-item-qty">{item.cantidad}</span>
                                                <button
                                                    className="store-cart-btn"
                                                    onClick={() => handleIncrementar(item)}
                                                    disabled={item.cantidad >= item.stock_disponible}
                                                >
                                                    +
                                                </button>
                                            </div>
                                            <span className="store-cart-item-subtotal">
                                                {formatearMoneda(item.subtotal)}
                                            </span>
                                            <button
                                                className="store-cart-item-remove"
                                                onClick={() => handleEliminarItem(item)}
                                                title="Eliminar"
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
                                <div className="store-cart-footer">
                                    <div className="store-cart-total">
                                        <span>Total:</span>
                                        <strong>{formatearMoneda(carrito.valor_total)}</strong>
                                    </div>
                                    <button
                                        className="btn btn-primary btn-block"
                                        onClick={handleConfirmarCompra}
                                        disabled={procesandoCompra}
                                    >
                                        {procesandoCompra ? (
                                            <>
                                                <span className="loading-spinner" />
                                                Procesando...
                                            </>
                                        ) : (
                                            'Confirmar Compra'
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
