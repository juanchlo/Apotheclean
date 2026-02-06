/**
 * Página de Gestión de Productos para Administrador.
 * Permite CRUD completo de productos con búsqueda y archivo.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
    listarProductos,
    crearProducto,
    actualizarProducto,
    eliminarProducto,
    subirImagenProducto,
    obtenerUrlImagenProducto,
    limpiarCacheProductos,
    restaurarProducto as restaurarProductoApi
} from '../../api/products.api';
import type { Producto, CrearProductoInput, ActualizarProductoInput } from '../../api/products.api';
import { ApiException } from '../../api/client';
import { AdminNavbar } from '../../components/layout/AdminNavbar';
import { ProductCard } from '../../components/common/ProductCard';
import './Products.css';

/**
 * Componente de página de productos.
 * Incluye listado con búsqueda, creación, edición y archivo.
 */
export function Products() {
    // Estado de productos
    const [productos, setProductos] = useState<Producto[]>([]);
    const [productosArchivados, setProductosArchivados] = useState<Producto[]>([]);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [exito, setExito] = useState<string | null>(null);

    // Estado de búsqueda
    const [busqueda, setBusqueda] = useState('');

    // Estado de vista (activos o archivados)
    const [vistaArchivados, setVistaArchivados] = useState(false);

    // Estado del modal de edición
    const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null);
    const [modoEdicion, setModoEdicion] = useState(false);
    const [datosEdicion, setDatosEdicion] = useState<ActualizarProductoInput>({});

    // Estado del modal de creación
    const [modalCrear, setModalCrear] = useState(false);
    const [datosNuevo, setDatosNuevo] = useState<CrearProductoInput>({
        nombre: '',
        barcode: '',
        valor_unitario: 0,
        stock: 0,
        descripcion: ''
    });
    const [imagenNueva, setImagenNueva] = useState<File | null>(null);
    const [imagenPreview, setImagenPreview] = useState<string | null>(null);
    const [erroresValidacion, setErroresValidacion] = useState<Record<string, string>>({});

    // Referencia para el input de imagen
    const inputImagenRef = useRef<HTMLInputElement>(null);
    const inputImagenNuevaRef = useRef<HTMLInputElement>(null);

    /**
     * Carga todos los productos desde la API.
     */
    const cargarProductos = useCallback(async () => {
        setCargando(true);
        setError(null);

        try {
            limpiarCacheProductos();

            // Cargar productos activos
            const respuesta = await listarProductos(1000, 0, false);
            setProductos(respuesta.productos);

            // Cargar productos archivados (eliminados)
            const respuestaArchivados = await listarProductos(1000, 0, true);
            setProductosArchivados(respuestaArchivados.productos);
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error al cargar los productos');
            }
        } finally {
            setCargando(false);
        }
    }, []);

    // Cargar productos al montar
    useEffect(() => {
        cargarProductos();
    }, [cargarProductos]);

    /**
     * Filtra productos según la búsqueda.
     */
    const productosFiltrados = productos.filter(p => {
        if (!busqueda.trim()) return true;
        const termino = busqueda.toLowerCase();
        return (
            p.nombre.toLowerCase().includes(termino) ||
            p.barcode.toLowerCase().includes(termino)
        );
    });

    /**
     * Filtra productos archivados según la búsqueda.
     */
    const archivadosFiltrados = productosArchivados.filter(p => {
        if (!busqueda.trim()) return true;
        const termino = busqueda.toLowerCase();
        return (
            p.nombre.toLowerCase().includes(termino) ||
            p.barcode.toLowerCase().includes(termino)
        );
    });

    /**
     * Abre el modal de visualización de producto.
     */
    const abrirModalProducto = (producto: Producto) => {
        setProductoSeleccionado(producto);
        setModoEdicion(false);
        setDatosEdicion({
            nombre: producto.nombre,
            valor_unitario: parseFloat(producto.valor_unitario),
            stock: producto.stock,
            descripcion: producto.descripcion ?? ''
        });
    };

    /**
     * Cierra el modal de producto.
     */
    const cerrarModalProducto = () => {
        setProductoSeleccionado(null);
        setModoEdicion(false);
        setDatosEdicion({});
    };

    /**
     * Activa el modo edición.
     */
    const activarEdicion = () => {
        setModoEdicion(true);
    };

    /**
     * Cancela la edición y restaura los datos originales.
     */
    const cancelarEdicion = () => {
        if (productoSeleccionado) {
            setDatosEdicion({
                nombre: productoSeleccionado.nombre,
                valor_unitario: parseFloat(productoSeleccionado.valor_unitario),
                stock: productoSeleccionado.stock,
                descripcion: productoSeleccionado.descripcion ?? ''
            });
        }
        setModoEdicion(false);
    };

    /**
     * Guarda los cambios del producto.
     */
    const guardarCambios = async () => {
        if (!productoSeleccionado) return;

        setCargando(true);
        setError(null);

        try {
            const productoActualizado = await actualizarProducto(
                productoSeleccionado.uuid,
                datosEdicion
            );

            // Actualizar en la lista local
            setProductos(prev =>
                prev.map(p => p.uuid === productoActualizado.uuid ? productoActualizado : p)
            );

            setProductoSeleccionado(productoActualizado);
            setModoEdicion(false);
            mostrarExito('Producto actualizado correctamente');
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error al actualizar el producto');
            }
        } finally {
            setCargando(false);
        }
    };

    /**
     * Archiva (soft delete) un producto.
     */
    const archivarProducto = async () => {
        if (!productoSeleccionado) return;

        setCargando(true);
        setError(null);

        try {
            await eliminarProducto(productoSeleccionado.uuid);

            // Mover a archivados localmente
            setProductosArchivados(prev => [...prev, productoSeleccionado]);
            setProductos(prev => prev.filter(p => p.uuid !== productoSeleccionado.uuid));

            cerrarModalProducto();
            mostrarExito('Producto archivado correctamente');
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error al archivar el producto');
            }
        } finally {
            setCargando(false);
        }
    };

    /**
     * Restaura un producto archivado.
     */
    const restaurarProducto = async (producto: Producto) => {
        setCargando(true);
        setError(null);

        try {
            await restaurarProductoApi(producto.uuid);

            // Mover a productos activos
            setProductos(prev => [...prev, producto]);
            setProductosArchivados(prev => prev.filter(p => p.uuid !== producto.uuid));

            mostrarExito('Producto restaurado correctamente');
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error al restaurar el producto');
            }
        } finally {
            setCargando(false);
        }
    };

    /**
     * Sube una nueva imagen al producto.
     */
    const subirImagen = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (!productoSeleccionado || !event.target.files?.[0]) return;

        const archivo = event.target.files[0];
        setCargando(true);
        setError(null);

        try {
            const productoActualizado = await subirImagenProducto(
                productoSeleccionado.uuid,
                archivo
            );

            setProductos(prev =>
                prev.map(p => p.uuid === productoActualizado.uuid ? productoActualizado : p)
            );
            setProductoSeleccionado(productoActualizado);
            mostrarExito('Imagen actualizada correctamente');
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Error al subir la imagen');
            }
        } finally {
            setCargando(false);
        }
    };

    /**
     * Abre el modal de creación.
     */
    const abrirModalCrear = () => {
        setModalCrear(true);
        setDatosNuevo({
            nombre: '',
            barcode: '',
            valor_unitario: 0,
            stock: 0,
            descripcion: ''
        });
        setImagenNueva(null);
        setImagenPreview(null);
        setErroresValidacion({});
    };

    /**
     * Cierra el modal de creación.
     */
    const cerrarModalCrear = () => {
        setModalCrear(false);
        setDatosNuevo({
            nombre: '',
            barcode: '',
            valor_unitario: 0,
            stock: 0,
            descripcion: ''
        });
        setImagenNueva(null);
        setImagenPreview(null);
        setErroresValidacion({});
    };

    /**
     * Maneja el cambio de imagen para nuevo producto.
     */
    const handleImagenNueva = (event: React.ChangeEvent<HTMLInputElement>) => {
        const archivo = event.target.files?.[0];
        if (archivo) {
            setImagenNueva(archivo);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagenPreview(reader.result as string);
            };
            reader.readAsDataURL(archivo);
        }
    };

    /**
     * Valida los datos del nuevo producto.
     */
    const validarNuevoProducto = (): boolean => {
        const errores: Record<string, string> = {};

        if (!datosNuevo.nombre.trim()) {
            errores.nombre = 'El nombre es obligatorio';
        }

        if (!datosNuevo.barcode.trim()) {
            errores.barcode = 'El código de barras es obligatorio';
        }

        if (datosNuevo.valor_unitario <= 0) {
            errores.valor_unitario = 'El precio debe ser mayor a 0';
        }

        if (datosNuevo.stock < 0) {
            errores.stock = 'El stock no puede ser negativo';
        }

        setErroresValidacion(errores);
        return Object.keys(errores).length === 0;
    };

    /**
     * Crea un nuevo producto.
     */
    const crearNuevoProducto = async () => {
        if (!validarNuevoProducto()) return;

        setCargando(true);
        setError(null);

        try {
            const productoCreado = await crearProducto(datosNuevo);

            // Subir imagen si se seleccionó
            if (imagenNueva) {
                await subirImagenProducto(productoCreado.uuid, imagenNueva);
            }

            // Recargar productos para obtener el estado actualizado
            await cargarProductos();

            cerrarModalCrear();
            mostrarExito('Producto creado correctamente');
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Error al crear el producto');
            }
        } finally {
            setCargando(false);
        }
    };

    /**
     * Muestra un mensaje de éxito temporal.
     */
    const mostrarExito = (mensaje: string) => {
        setExito(mensaje);
        setTimeout(() => setExito(null), 3000);
    };



    return (
        <div className="products-page">
            {/* Header */}
            {/* Header */}
            <AdminNavbar />

            {/* Contenido principal */}
            <main className="products-main">
                <div className="products-container">
                    {/* Título y acciones */}
                    <div className="products-title-section">
                        <div>
                            <h1>Gestión de Productos</h1>
                            <p>Administra el inventario de tu farmacia</p>
                        </div>
                        <button className="btn btn-primary" onClick={abrirModalCrear}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="12" y1="5" x2="12" y2="19" />
                                <line x1="5" y1="12" x2="19" y2="12" />
                            </svg>
                            Nuevo Producto
                        </button>
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

                    {/* Barra de búsqueda y filtros */}
                    <div className="products-toolbar card">
                        <div className="products-search">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="11" cy="11" r="8" />
                                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                            </svg>
                            <input
                                type="text"
                                className="input"
                                placeholder="Buscar por nombre o código de barras..."
                                value={busqueda}
                                onChange={(e) => setBusqueda(e.target.value)}
                            />
                        </div>

                        <div className="products-view-toggle">
                            <button
                                className={`products-view-btn ${!vistaArchivados ? 'active' : ''}`}
                                onClick={() => setVistaArchivados(false)}
                            >
                                Activos ({productos.length})
                            </button>
                            <button
                                className={`products-view-btn ${vistaArchivados ? 'active' : ''}`}
                                onClick={() => setVistaArchivados(true)}
                            >
                                Archivados ({productosArchivados.length})
                            </button>
                        </div>
                    </div>

                    {/* Grid de productos */}
                    {cargando && productos.length === 0 ? (
                        <div className="products-loading">
                            <span className="loading-spinner" />
                            Cargando productos...
                        </div>
                    ) : (
                        <div className="products-grid">
                            {(vistaArchivados ? archivadosFiltrados : productosFiltrados).length === 0 ? (
                                <div className="products-empty">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                                        <line x1="12" y1="22.08" x2="12" y2="12" />
                                    </svg>
                                    <p>
                                        {busqueda
                                            ? 'No se encontraron productos con ese término'
                                            : vistaArchivados
                                                ? 'No hay productos archivados'
                                                : 'No hay productos registrados'}
                                    </p>
                                    {!vistaArchivados && !busqueda && (
                                        <button className="btn btn-primary" onClick={abrirModalCrear}>
                                            Crear primer producto
                                        </button>
                                    )}
                                </div>
                            ) : (
                                (vistaArchivados ? archivadosFiltrados : productosFiltrados).map((producto) => (
                                    <ProductCard
                                        key={producto.uuid}
                                        producto={producto}
                                        onClick={() => !vistaArchivados && abrirModalProducto(producto)}
                                        variant={vistaArchivados ? 'archived' : 'default'}
                                        actions={vistaArchivados && (
                                            <button
                                                className="btn btn-secondary product-card-restore"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    restaurarProducto(producto);
                                                }}
                                            >
                                                Restaurar
                                            </button>
                                        )}
                                    />
                                ))
                            )}
                        </div>
                    )}
                </div>
            </main>

            {/* Modal de detalle/edición de producto */}
            {productoSeleccionado && (
                <div className="modal-overlay" onClick={cerrarModalProducto}>
                    <div className="modal product-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{modoEdicion ? 'Editar Producto' : 'Detalle del Producto'}</h2>
                            <button className="modal-close" onClick={cerrarModalProducto}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>

                        <div className="modal-body">
                            {/* Imagen */}
                            <div className="product-modal-image">
                                {productoSeleccionado.imagen_uuid ? (
                                    <img
                                        src={obtenerUrlImagenProducto(productoSeleccionado.uuid)}
                                        alt={productoSeleccionado.nombre}
                                    />
                                ) : (
                                    <div className="product-modal-placeholder">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                            <circle cx="8.5" cy="8.5" r="1.5" />
                                            <polyline points="21 15 16 10 5 21" />
                                        </svg>
                                        <span>Sin imagen</span>
                                    </div>
                                )}
                                {modoEdicion && (
                                    <>
                                        <input
                                            ref={inputImagenRef}
                                            type="file"
                                            accept="image/*"
                                            style={{ display: 'none' }}
                                            onChange={subirImagen}
                                        />
                                        <button
                                            className="btn btn-secondary product-modal-change-image"
                                            onClick={() => inputImagenRef.current?.click()}
                                        >
                                            Cambiar imagen
                                        </button>
                                    </>
                                )}
                            </div>

                            {/* Campos */}
                            <div className="product-modal-fields">
                                {/* Nombre */}
                                <div className="input-group">
                                    <label className="input-label">Nombre</label>
                                    {modoEdicion ? (
                                        <input
                                            type="text"
                                            className="input"
                                            value={datosEdicion.nombre ?? ''}
                                            onChange={(e) => setDatosEdicion({ ...datosEdicion, nombre: e.target.value })}
                                        />
                                    ) : (
                                        <p className="product-modal-value">{productoSeleccionado.nombre}</p>
                                    )}
                                </div>

                                {/* Código de barras (siempre readonly) */}
                                <div className="input-group">
                                    <label className="input-label">Código de Barras</label>
                                    <p className="product-modal-value product-modal-barcode">
                                        {productoSeleccionado.barcode}
                                        <span className="immutable-badge">Inmutable</span>
                                    </p>
                                </div>

                                {/* Precio */}
                                <div className="input-group">
                                    <label className="input-label">Precio Unitario</label>
                                    {modoEdicion ? (
                                        <input
                                            type="number"
                                            className="input"
                                            min="0"
                                            step="100"
                                            value={datosEdicion.valor_unitario ?? 0}
                                            onChange={(e) => setDatosEdicion({ ...datosEdicion, valor_unitario: parseFloat(e.target.value) || 0 })}
                                        />
                                    ) : (
                                        <p className="product-modal-value">
                                            {typeof productoSeleccionado.valor_unitario === 'string'
                                                ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(parseFloat(productoSeleccionado.valor_unitario))
                                                : new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(productoSeleccionado.valor_unitario)
                                            }
                                        </p>
                                    )}
                                </div>

                                {/* Stock */}
                                <div className="input-group">
                                    <label className="input-label">Stock</label>
                                    {modoEdicion ? (
                                        <input
                                            type="number"
                                            className="input"
                                            min="0"
                                            value={datosEdicion.stock ?? 0}
                                            onChange={(e) => setDatosEdicion({ ...datosEdicion, stock: parseInt(e.target.value) || 0 })}
                                        />
                                    ) : (
                                        <p className={`product-modal-value ${productoSeleccionado.stock <= 5 ? 'stock-low' : ''}`}>
                                            {productoSeleccionado.stock} unidades
                                            {productoSeleccionado.stock <= 5 && <span className="stock-warning">Stock bajo</span>}
                                        </p>
                                    )}
                                </div>

                                {/* Descripción */}
                                <div className="input-group">
                                    <label className="input-label">Descripción</label>
                                    {modoEdicion ? (
                                        <textarea
                                            className="input textarea"
                                            rows={3}
                                            value={datosEdicion.descripcion ?? ''}
                                            onChange={(e) => setDatosEdicion({ ...datosEdicion, descripcion: e.target.value })}
                                            placeholder="Descripción del producto..."
                                        />
                                    ) : (
                                        <p className="product-modal-value product-modal-desc">
                                            {productoSeleccionado.descripcion || 'Sin descripción'}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            {modoEdicion ? (
                                <>
                                    <button className="btn btn-secondary" onClick={cancelarEdicion}>
                                        Cancelar
                                    </button>
                                    <button className="btn btn-primary" onClick={guardarCambios} disabled={cargando}>
                                        {cargando ? 'Guardando...' : 'Guardar Cambios'}
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button className="btn btn-danger" onClick={archivarProducto} disabled={cargando}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                        Archivar
                                    </button>
                                    <button className="btn btn-primary" onClick={activarEdicion}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                        Editar
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de creación de producto */}
            {modalCrear && (
                <div className="modal-overlay" onClick={cerrarModalCrear}>
                    <div className="modal product-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Nuevo Producto</h2>
                            <button className="modal-close" onClick={cerrarModalCrear}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>

                        <div className="modal-body">
                            {/* Imagen */}
                            <div className="product-modal-image">
                                {imagenPreview ? (
                                    <img src={imagenPreview} alt="Preview" />
                                ) : (
                                    <div className="product-modal-placeholder">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                            <circle cx="8.5" cy="8.5" r="1.5" />
                                            <polyline points="21 15 16 10 5 21" />
                                        </svg>
                                        <span>Sin imagen</span>
                                    </div>
                                )}
                                <input
                                    ref={inputImagenNuevaRef}
                                    type="file"
                                    accept="image/*"
                                    style={{ display: 'none' }}
                                    onChange={handleImagenNueva}
                                />
                                <button
                                    className="btn btn-secondary product-modal-change-image"
                                    onClick={() => inputImagenNuevaRef.current?.click()}
                                >
                                    {imagenPreview ? 'Cambiar imagen' : 'Seleccionar imagen'}
                                </button>
                            </div>

                            {/* Campos */}
                            <div className="product-modal-fields">
                                {/* Nombre */}
                                <div className="input-group">
                                    <label className="input-label">Nombre *</label>
                                    <input
                                        type="text"
                                        className={`input ${erroresValidacion.nombre ? 'input-error' : ''}`}
                                        value={datosNuevo.nombre}
                                        onChange={(e) => setDatosNuevo({ ...datosNuevo, nombre: e.target.value })}
                                        placeholder="Nombre del producto"
                                    />
                                    {erroresValidacion.nombre && (
                                        <span className="input-error-msg">{erroresValidacion.nombre}</span>
                                    )}
                                </div>

                                {/* Código de barras */}
                                <div className="input-group">
                                    <label className="input-label">Código de Barras *</label>
                                    <input
                                        type="text"
                                        className={`input ${erroresValidacion.barcode ? 'input-error' : ''}`}
                                        value={datosNuevo.barcode}
                                        onChange={(e) => setDatosNuevo({ ...datosNuevo, barcode: e.target.value })}
                                        placeholder="Código de barras único"
                                    />
                                    {erroresValidacion.barcode && (
                                        <span className="input-error-msg">{erroresValidacion.barcode}</span>
                                    )}
                                </div>

                                {/* Precio */}
                                <div className="input-group">
                                    <label className="input-label">Precio Unitario (COP) *</label>
                                    <input
                                        type="number"
                                        className={`input ${erroresValidacion.valor_unitario ? 'input-error' : ''}`}
                                        min="0"
                                        step="100"
                                        value={datosNuevo.valor_unitario}
                                        onChange={(e) => setDatosNuevo({ ...datosNuevo, valor_unitario: parseFloat(e.target.value) || 0 })}
                                        placeholder="0"
                                    />
                                    {erroresValidacion.valor_unitario && (
                                        <span className="input-error-msg">{erroresValidacion.valor_unitario}</span>
                                    )}
                                </div>

                                {/* Stock */}
                                <div className="input-group">
                                    <label className="input-label">Stock Inicial</label>
                                    <input
                                        type="number"
                                        className={`input ${erroresValidacion.stock ? 'input-error' : ''}`}
                                        min="0"
                                        value={datosNuevo.stock}
                                        onChange={(e) => setDatosNuevo({ ...datosNuevo, stock: parseInt(e.target.value) || 0 })}
                                        placeholder="0"
                                    />
                                    {erroresValidacion.stock && (
                                        <span className="input-error-msg">{erroresValidacion.stock}</span>
                                    )}
                                </div>

                                {/* Descripción */}
                                <div className="input-group">
                                    <label className="input-label">Descripción</label>
                                    <textarea
                                        className="input textarea"
                                        rows={3}
                                        value={datosNuevo.descripcion}
                                        onChange={(e) => setDatosNuevo({ ...datosNuevo, descripcion: e.target.value })}
                                        placeholder="Descripción del producto (opcional)"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={cerrarModalCrear}>
                                Cancelar
                            </button>
                            <button className="btn btn-primary" onClick={crearNuevoProducto} disabled={cargando}>
                                {cargando ? 'Creando...' : 'Crear Producto'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
