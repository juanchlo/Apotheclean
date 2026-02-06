import React from 'react';
import { obtenerUrlImagenProducto } from '../../api/products.api';
import type { Producto } from '../../api/products.api';
import './ProductCard.css';

interface ProductCardProps {
    producto: Producto;
    onClick?: () => void;
    actions?: React.ReactNode;
    className?: string;
    variant?: 'default' | 'archived' | 'no-hover';
}

/**
 * Componente reutilizable para mostrar un producto en forma de card.
 */
export function ProductCard({
    producto,
    onClick,
    actions,
    className = '',
    variant = 'default'
}: ProductCardProps) {

    const formatearMoneda = (valor: string | number): string => {
        const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(numero);
    };

    return (
        <div
            className={`product-card ${variant !== 'default' ? variant : ''} ${className}`}
            onClick={onClick}
        >
            <div className="product-card-image">
                {producto.imagen_uuid ? (
                    <img
                        src={obtenerUrlImagenProducto(producto.uuid)}
                        alt={producto.nombre}
                        onError={(e) => {
                            (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23f0f0f0" width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="%23999" font-size="10">Sin imagen</text></svg>';
                        }}
                    />
                ) : (
                    <div className="product-card-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                            <circle cx="8.5" cy="8.5" r="1.5" />
                            <polyline points="21 15 16 10 5 21" />
                        </svg>
                    </div>
                )}
            </div>
            <div className="product-card-info">
                <h3 className="product-card-name" title={producto.nombre}>{producto.nombre}</h3>
                <p className="product-card-barcode">{producto.barcode}</p>
                <div className="product-card-meta">
                    <span className="product-card-price">
                        {formatearMoneda(producto.valor_unitario)}
                    </span>
                    <span className={`product-card-stock ${producto.stock <= 5 ? 'low' : ''}`}>
                        {producto.stock} unid.
                    </span>
                </div>
            </div>
            {actions && (
                <div className="product-card-actions" onClick={(e) => e.stopPropagation()}>
                    {actions}
                </div>
            )}
        </div>
    );
}
