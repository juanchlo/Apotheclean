/**
 * Página de Gestión de Ventas para Administrador.
 * Implementación pendiente.
 */

import { useState } from 'react';
import './Products.css'; // Reutilizamos estilos por ahora

export function Sales() {
    return (
        <div className="products-page">
            <header className="products-header">
                <div className="products-header-content">
                    <div className="products-logo">
                        <span>Apotheclean</span>
                    </div>
                    <nav className="products-nav">
                        <a href="/admin/reportes" className="products-nav-link">Reportes</a>
                        <a href="/admin/productos" className="products-nav-link">Productos</a>
                        <a href="/admin/ventas" className="products-nav-link active">Ventas</a>
                    </nav>
                </div>
            </header>
            <main className="products-main">
                <div className="products-container">
                    <h1>Gestión de Ventas</h1>
                    <p>Módulo en construcción...</p>
                </div>
            </main>
        </div>
    );
}
