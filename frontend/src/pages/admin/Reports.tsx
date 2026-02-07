/**
 * Página de Reportes de Ventas para Administrador.
 * Muestra filtros, gráfico pie y listado de ventas.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { obtenerReporteVentas } from '../../api/sales.api';
import type { Venta, ReporteVentasParams, ItemVenta } from '../../api/sales.api';
import { obtenerProductosBatch, obtenerUrlImagenProducto } from '../../api/products.api';
import type { Producto } from '../../api/products.api';
import { ApiException } from '../../api/client';
import { AdminNavbar } from '../../components/layout/AdminNavbar';
import './Reports.css';

/** Colores para el gráfico pie */
const CHART_COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#6B7280'];

/** Datos para el gráfico pie */
interface ProductoVendido {
    nombre: string;
    barcode: string;
    cantidad: number;
    detalleOtros?: { nombre: string; cantidad: number }[];
}

/** Posición del tooltip de producto */
interface TooltipPosition {
    x: number;
    y: number;
}

/**
 * Componente de página de reportes.
 * Incluye filtros, gráfico y tabla de ventas.
 */
export function Reports() {
    // Estado de filtros
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [modalidad, setModalidad] = useState<'virtual' | 'fisica' | ''>('');
    const [estado, setEstado] = useState<'pendiente' | 'completada' | 'cancelada' | ''>('');

    // Estado de datos
    const [ventas, setVentas] = useState<Venta[]>([]);
    const [todasLasVentas, setTodasLasVentas] = useState<Venta[]>([]); // Para el gráfico
    const [totalVentas, setTotalVentas] = useState(0);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Estado de productos cargados
    const [productosMap, setProductosMap] = useState<Map<string, Producto>>(new Map());

    // Estado de paginación
    const [limite] = useState(12);
    const [offset, setOffset] = useState(0);

    // Estado del modal de detalle
    const [ventaSeleccionada, setVentaSeleccionada] = useState<Venta | null>(null);

    // Estado del tooltip de producto
    const [productoHover, setProductoHover] = useState<ItemVenta | null>(null);
    const [tooltipPos, setTooltipPos] = useState<TooltipPosition>({ x: 0, y: 0 });
    const tooltipRef = useRef<HTMLDivElement>(null);

    /**
     * Carga las ventas paginadas para la tabla.
     */
    const cargarVentasPaginadas = useCallback(async () => {
        setCargando(true);
        setError(null);

        try {
            const params: ReporteVentasParams = { limite, offset };
            if (modalidad) params.modalidad = modalidad;
            if (estado) params.estado = estado;
            if (fechaInicio) params.fecha_inicio = fechaInicio;
            if (fechaFin) params.fecha_fin = fechaFin;

            const respuesta = await obtenerReporteVentas(params);
            setVentas(respuesta.ventas);
            // setTotalVentas(respuesta.total); // Usamos el total de 'todasLasVentas' para evitar paginación incorrecta

            // Extraer IDs de productos únicos de las ventas paginadas
            const productosIds = new Set<string>();
            respuesta.ventas.forEach(venta => {
                venta.items.forEach(item => {
                    productosIds.add(item.producto_id);
                });
            });

            // Cargar información de productos
            if (productosIds.size > 0) {
                const productos = await obtenerProductosBatch(Array.from(productosIds));
                setProductosMap(prev => new Map([...prev, ...productos]));
            }
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error al cargar las ventas');
            }
        } finally {
            setCargando(false);
        }
    }, [limite, offset, modalidad, estado, fechaInicio, fechaFin]);

    /**
     * Carga TODAS las ventas para el gráfico (sin paginación).
     * Solo se ejecuta cuando cambian los filtros, no cuando cambia el offset.
     */
    const cargarTodasLasVentas = useCallback(async () => {
        try {
            const params: ReporteVentasParams = { limite: 10000, offset: 0 };
            if (modalidad) params.modalidad = modalidad;
            if (estado) params.estado = estado;
            if (fechaInicio) params.fecha_inicio = fechaInicio;
            if (fechaFin) params.fecha_fin = fechaFin;

            const respuesta = await obtenerReporteVentas(params);
            setTodasLasVentas(respuesta.ventas);
            setTotalVentas(respuesta.total);

            // Extraer IDs de productos únicos de todas las ventas
            const productosIds = new Set<string>();
            respuesta.ventas.forEach(venta => {
                venta.items.forEach(item => {
                    productosIds.add(item.producto_id);
                });
            });

            // Cargar información de productos
            if (productosIds.size > 0) {
                const productos = await obtenerProductosBatch(Array.from(productosIds));
                setProductosMap(prev => new Map([...prev, ...productos]));
            }
        } catch (err) {
            console.error('Error al cargar todas las ventas para el gráfico:', err);
        }
    }, [modalidad, estado, fechaInicio, fechaFin]); // Sin limite ni offset

    // Cargar ventas paginadas cuando cambia offset o filtros
    useEffect(() => {
        cargarVentasPaginadas();
    }, [cargarVentasPaginadas]);

    // Cargar todas las ventas solo cuando cambian los filtros (no el offset)
    useEffect(() => {
        cargarTodasLasVentas();
    }, [cargarTodasLasVentas]);

    /**
     * Aplica los filtros y reinicia la paginación.
     */
    const aplicarFiltros = () => {
        setOffset(0);
        // cargarVentasPaginadas y cargarTodasLasVentas se ejecutarán automáticamente
    };

    /**
     * Limpia todos los filtros.
     */
    const limpiarFiltros = () => {
        setFechaInicio('');
        setFechaFin('');
        setModalidad('');
        setEstado('');
        setOffset(0);
    };

    /**
     * Obtiene el nombre de un producto desde el mapa cacheado.
     */
    const obtenerNombreProducto = (productoId: string): string => {
        const producto = productosMap.get(productoId);
        return producto?.nombre ?? 'Producto desconocido';
    };

    /**
     * Obtiene el código de barras de un producto desde el mapa cacheado.
     */
    const obtenerBarcodeProducto = (productoId: string): string => {
        const producto = productosMap.get(productoId);
        return producto?.barcode ?? '---';
    };

    /**
     * Calcula datos para el gráfico pie.
     * Agrupa TODAS las ventas por productos y muestra top 5 + otros.
     */
    const calcularDatosGrafico = (): ProductoVendido[] => {
        // Agregar todas las cantidades por producto usando TODAS las ventas
        const productosConteo = new Map<string, number>();

        todasLasVentas.forEach(venta => {
            venta.items.forEach(item => {
                const actual = productosConteo.get(item.producto_id) || 0;
                productosConteo.set(item.producto_id, actual + item.cantidad);
            });
        });

        // Convertir a array con nombres reales
        const productos = Array.from(productosConteo.entries())
            .map(([id, cantidad]) => ({
                nombre: obtenerNombreProducto(id),
                barcode: obtenerBarcodeProducto(id),
                cantidad
            }))
            .sort((a, b) => b.cantidad - a.cantidad);

        // Tomar top 5 y agrupar el resto en "Otros"
        if (productos.length <= 6) {
            return productos;
        }

        const top5 = productos.slice(0, 5);
        const otrosItems = productos.slice(5);
        const otrosCantidad = otrosItems.reduce((sum, p) => sum + p.cantidad, 0);

        return [
            ...top5,
            {
                nombre: 'Otros',
                barcode: '',
                cantidad: otrosCantidad,
                detalleOtros: otrosItems.map(p => ({
                    nombre: p.nombre,
                    cantidad: p.cantidad
                }))
            }
        ];
    };

    const datosGrafico = calcularDatosGrafico();

    /**
     * Formatea una fecha ISO a formato legible.
     */
    const formatearFecha = (fecha: string): string => {
        return new Date(fecha).toLocaleDateString('es-CO', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    /**
     * Formatea un valor en COP.
     */
    const formatearMoneda = (valor: string): string => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(parseFloat(valor));
    };

    /**
     * Maneja el hover sobre un item de venta.
     */
    const handleItemHover = (item: ItemVenta, event: React.MouseEvent) => {
        const rect = event.currentTarget.getBoundingClientRect();
        setTooltipPos({
            x: rect.right + 10,
            y: rect.top
        });
        setProductoHover(item);
    };

    /**
     * Maneja la salida del hover.
     */
    const handleItemLeave = () => {
        setProductoHover(null);
    };



    // Calular total de items vendidos para porcentajes
    const totalItemsVendidos = todasLasVentas.reduce((acc, venta) => {
        return acc + venta.items.reduce((sum, item) => sum + item.cantidad, 0);
    }, 0);

    /**
     * Renderiza el tooltip personalizado para el gráfico.
     */
    const renderCustomTooltip = (props: { active?: boolean; payload?: ReadonlyArray<{ payload: ProductoVendido }> }) => {
        const { active, payload } = props;
        if (active && payload && payload.length > 0) {
            const data = payload[0].payload;
            return (
                <div className="chart-tooltip">
                    <p className="chart-tooltip-name">{data.nombre}</p>
                    {data.barcode && (
                        <p className="chart-tooltip-barcode">{data.barcode}</p>
                    )}
                    <p className="chart-tooltip-cantidad">
                        {data.cantidad} unidades
                        {totalItemsVendidos > 0 && (
                            <span className="chart-tooltip-percentage">
                                ({((data.cantidad / totalItemsVendidos) * 100).toFixed(1)}%)
                            </span>
                        )}
                    </p>

                    {/* Detalle para "Otros" */}
                    {data.detalleOtros && data.detalleOtros.length > 0 && (
                        <div className="chart-tooltip-others">
                            <p className="chart-tooltip-others-title">Incluye:</p>
                            <ul className="chart-tooltip-others-list">
                                {data.detalleOtros.slice(0, 10).map((item, idx) => (
                                    <li key={idx}>
                                        <div className="chart-tooltip-others-item-name">
                                            {item.nombre}
                                        </div>
                                        <div className="chart-tooltip-others-item-stats">
                                            <strong>{item.cantidad}</strong>
                                            {totalItemsVendidos > 0 && (
                                                <span className="chart-tooltip-percentage-sm">
                                                    ({((item.cantidad / totalItemsVendidos) * 100).toFixed(1)}%)
                                                </span>
                                            )}
                                        </div>
                                    </li>
                                ))}
                                {data.detalleOtros.length > 10 && (
                                    <li className="chart-tooltip-others-more">
                                        ... y {data.detalleOtros.length - 10} más
                                    </li>
                                )}
                            </ul>
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="reports-page">
            {/* Header */}
            {/* Header */}
            <AdminNavbar />

            {/* Contenido principal */}
            <main className="reports-main">
                <div className="reports-container">
                    {/* Título */}
                    <div className="reports-title-section">
                        <h1>Reportes de Ventas</h1>
                        <p>Analiza el rendimiento de ventas de tu farmacia</p>
                    </div>

                    {/* Filtros */}
                    <section className="reports-filters card">
                        <h2>Filtros</h2>

                        <div className="reports-filters-grid">
                            {/* Fecha inicio */}
                            <div className="input-group">
                                <label htmlFor="fechaInicio" className="input-label">
                                    Fecha inicio
                                </label>
                                <input
                                    id="fechaInicio"
                                    type="date"
                                    className="input"
                                    value={fechaInicio}
                                    onChange={(e) => setFechaInicio(e.target.value)}
                                />
                            </div>

                            {/* Fecha fin */}
                            <div className="input-group">
                                <label htmlFor="fechaFin" className="input-label">
                                    Fecha fin
                                </label>
                                <input
                                    id="fechaFin"
                                    type="date"
                                    className="input"
                                    value={fechaFin}
                                    onChange={(e) => setFechaFin(e.target.value)}
                                />
                            </div>

                            {/* Modalidad */}
                            <div className="input-group">
                                <label htmlFor="modalidad" className="input-label">
                                    Modalidad
                                </label>
                                <select
                                    id="modalidad"
                                    className="input"
                                    value={modalidad}
                                    onChange={(e) => setModalidad(e.target.value as 'virtual' | 'fisica' | '')}
                                >
                                    <option value="">Todas</option>
                                    <option value="virtual">Virtual</option>
                                    <option value="fisica">Física</option>
                                </select>
                            </div>

                            {/* Estado */}
                            <div className="input-group">
                                <label htmlFor="estado" className="input-label">
                                    Estado
                                </label>
                                <select
                                    id="estado"
                                    className="input"
                                    value={estado}
                                    onChange={(e) => setEstado(e.target.value as 'pendiente' | 'completada' | 'cancelada' | '')}
                                >
                                    <option value="">Todos</option>
                                    <option value="pendiente">Pendiente</option>
                                    <option value="completada">Completada</option>
                                    <option value="cancelada">Cancelada</option>
                                </select>
                            </div>
                        </div>

                        <div className="reports-filters-actions">
                            <button
                                className="btn btn-secondary"
                                onClick={limpiarFiltros}
                            >
                                Limpiar
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={aplicarFiltros}
                                disabled={cargando}
                            >
                                Aplicar filtros
                            </button>
                        </div>
                    </section>

                    {/* Gráfico y estadísticas */}
                    <div className="reports-stats-grid">
                        {/* Gráfico Pie */}
                        <section className="reports-chart card">
                            <h2>Top Productos Vendidos</h2>

                            {datosGrafico.length > 0 ? (
                                <div className="reports-chart-container">
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={datosGrafico}
                                                dataKey="cantidad"
                                                nameKey="nombre"
                                                cx="50%"
                                                cy="50%"
                                                outerRadius={100}
                                            >
                                                {datosGrafico.map((_, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                                                    />
                                                ))}
                                            </Pie>
                                            <Tooltip content={renderCustomTooltip} />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div className="reports-empty">
                                    <p>No hay datos para mostrar</p>
                                </div>
                            )}
                        </section>

                        {/* Resumen */}
                        <section className="reports-summary card">
                            <h2>Resumen</h2>

                            <div className="reports-summary-stats">
                                <div className="reports-summary-stat">
                                    <span className="reports-summary-value">{totalVentas}</span>
                                    <span className="reports-summary-label">Total ventas</span>
                                </div>

                                <div className="reports-summary-stat">
                                    <span className="reports-summary-value">
                                        {formatearMoneda(
                                            todasLasVentas
                                                .reduce((sum, v) => sum + parseFloat(v.valor_total_cop), 0)
                                                .toString()
                                        )}
                                    </span>
                                    <span className="reports-summary-label">Valor total</span>
                                </div>

                                <div className="reports-summary-stat">
                                    <span className="reports-summary-value">
                                        {todasLasVentas.filter(v => v.estado === 'completada').length}
                                    </span>
                                    <span className="reports-summary-label">Completadas</span>
                                </div>

                                <div className="reports-summary-stat">
                                    <span className="reports-summary-value">
                                        {todasLasVentas.filter(v => v.estado === 'pendiente').length}
                                    </span>
                                    <span className="reports-summary-label">Pendientes</span>
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Mensaje de error */}
                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {/* Listado de ventas */}
                    <section className="reports-list card">
                        <h2>Listado de Ventas</h2>

                        {cargando ? (
                            <div className="reports-loading">
                                <span className="loading-spinner" />
                                Cargando ventas...
                            </div>
                        ) : ventas.length === 0 ? (
                            <div className="reports-empty">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                    <polyline points="17 8 12 3 7 8" />
                                    <line x1="12" y1="3" x2="12" y2="15" />
                                </svg>
                                <p>No se encontraron ventas</p>
                            </div>
                        ) : (
                            <>
                                {/* Cards de ventas */}
                                <div className="reports-sales-grid">
                                    {ventas.map((venta) => (
                                        <div
                                            key={venta.uuid}
                                            className="reports-sale-card"
                                            onClick={() => setVentaSeleccionada(venta)}
                                        >
                                            <div className="reports-sale-header">
                                                <span className={`reports-sale-badge reports-sale-badge-${venta.estado}`}>
                                                    {venta.estado}
                                                </span>
                                                <span className="reports-sale-modalidad">
                                                    {venta.modalidad}
                                                </span>
                                            </div>

                                            <div className="reports-sale-body">
                                                <p className="reports-sale-id">
                                                    #{venta.uuid.substring(0, 8)}
                                                </p>
                                                <p className="reports-sale-fecha">
                                                    {formatearFecha(venta.fecha)}
                                                </p>
                                                {/* Mostrar nombres de productos */}
                                                <div className="reports-sale-productos">
                                                    {venta.items.slice(0, 2).map((item, idx) => (
                                                        <span key={idx} className="reports-sale-producto">
                                                            {obtenerNombreProducto(item.producto_id)}
                                                        </span>
                                                    ))}
                                                    {venta.items.length > 2 && (
                                                        <span className="reports-sale-producto-mas">
                                                            +{venta.items.length - 2} más
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="reports-sale-footer">
                                                <span className="reports-sale-items">
                                                    {venta.items.length} item{venta.items.length !== 1 ? 's' : ''}
                                                </span>
                                                <span className="reports-sale-total">
                                                    {formatearMoneda(venta.valor_total_cop)}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Paginación */}
                                <div className="reports-pagination">
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => setOffset(Math.max(0, offset - limite))}
                                        disabled={offset === 0}
                                    >
                                        Anterior
                                    </button>

                                    <span className="reports-pagination-info">
                                        Mostrando {offset + 1} - {Math.min(offset + limite, totalVentas)} de {totalVentas}
                                    </span>

                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => setOffset(offset + limite)}
                                        disabled={offset + limite >= totalVentas}
                                    >
                                        Siguiente
                                    </button>
                                </div>
                            </>
                        )}
                    </section>
                </div>
            </main>

            {/* Modal de detalle de venta */}
            {ventaSeleccionada && (
                <div className="reports-modal-overlay" onClick={() => setVentaSeleccionada(null)}>
                    <div className="reports-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="reports-modal-header">
                            <h2>Detalle de Venta</h2>
                            <button
                                className="reports-modal-close"
                                onClick={() => setVentaSeleccionada(null)}
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>

                        <div className="reports-modal-body">
                            <div className="reports-modal-info">
                                <div className="reports-modal-row">
                                    <span>ID:</span>
                                    <span>{ventaSeleccionada.uuid}</span>
                                </div>
                                <div className="reports-modal-row">
                                    <span>Fecha:</span>
                                    <span>{formatearFecha(ventaSeleccionada.fecha)}</span>
                                </div>
                                <div className="reports-modal-row">
                                    <span>Estado:</span>
                                    <span className={`reports-sale-badge reports-sale-badge-${ventaSeleccionada.estado}`}>
                                        {ventaSeleccionada.estado}
                                    </span>
                                </div>
                                <div className="reports-modal-row">
                                    <span>Modalidad:</span>
                                    <span>{ventaSeleccionada.modalidad}</span>
                                </div>
                            </div>

                            <h3>Items</h3>
                            <table className="reports-modal-table">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th>Cantidad</th>
                                        <th>Precio</th>
                                        <th>Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ventaSeleccionada.items.map((item, index) => (
                                        <tr
                                            key={index}
                                            className="reports-modal-item-row"
                                            onMouseEnter={(e) => handleItemHover(item, e)}
                                            onMouseLeave={handleItemLeave}
                                        >
                                            <td>
                                                <div className="product-cell">
                                                    <span className="product-name">{obtenerNombreProducto(item.producto_id)}</span>
                                                    <span className="product-barcode">{obtenerBarcodeProducto(item.producto_id)}</span>
                                                </div>
                                            </td>
                                            <td>{item.cantidad}</td>
                                            <td>{formatearMoneda(item.precio_unitario)}</td>
                                            <td>{formatearMoneda(item.subtotal)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            <div className="reports-modal-total">
                                <span>Total:</span>
                                <span>{formatearMoneda(ventaSeleccionada.valor_total_cop)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Tooltip flotante de producto */}
            {productoHover && (
                <div
                    ref={tooltipRef}
                    className="product-tooltip"
                    style={{
                        position: 'fixed',
                        left: `${tooltipPos.x}px`,
                        top: `${tooltipPos.y}px`,
                    }}
                >
                    <div className="product-tooltip-image">
                        {productosMap.get(productoHover.producto_id)?.imagen_uuid ? (
                            <img
                                src={obtenerUrlImagenProducto(productoHover.producto_id)}
                                alt={obtenerNombreProducto(productoHover.producto_id)}
                                onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23f0f0f0" width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="%23999" font-size="12">Sin imagen</text></svg>';
                                }}
                            />
                        ) : (
                            <div className="product-tooltip-placeholder">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                    <circle cx="8.5" cy="8.5" r="1.5" />
                                    <polyline points="21 15 16 10 5 21" />
                                </svg>
                                <span>Sin imagen</span>
                            </div>
                        )}
                    </div>
                    <div className="product-tooltip-info">
                        <h4>{obtenerNombreProducto(productoHover.producto_id)}</h4>
                        <p className="product-tooltip-barcode">
                            <strong>Código:</strong> {obtenerBarcodeProducto(productoHover.producto_id)}
                        </p>
                        <p className="product-tooltip-precio">
                            <strong>Precio:</strong> {formatearMoneda(productoHover.precio_unitario)}
                        </p>
                        <p className="product-tooltip-cantidad">
                            <strong>Cantidad:</strong> {productoHover.cantidad}
                        </p>
                        <p className="product-tooltip-subtotal">
                            <strong>Subtotal:</strong> {formatearMoneda(productoHover.subtotal)}
                        </p>
                        {productosMap.get(productoHover.producto_id)?.descripcion && (
                            <p className="product-tooltip-desc">
                                {productosMap.get(productoHover.producto_id)?.descripcion}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}