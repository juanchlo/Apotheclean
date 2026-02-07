import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { obtenerUsuarioActual, logout } from '../../api/auth.api';
import './UserNavbar.css';

/**
 * Componente de barra de navegación para el portal de usuarios.
 * Muestra mensaje de bienvenida y menú de cuenta.
 */
export function UserNavbar() {
    const navigate = useNavigate();
    const usuario = obtenerUsuarioActual();
    const [menuAbierto, setMenuAbierto] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleDeshabilitarCuenta = () => {
        if (window.confirm('¿Estás seguro de que deseas deshabilitar tu cuenta? Deberás contactar a un administrador para reactivarla.')) {
            // TODO: Implementar endpoint de deshabilitar cuenta si existe
            alert('Funcionalidad en desarrollo. Contacte al administrador.');
        }
    };

    return (
        <header className="user-header">
            <div className="user-header-content">
                {/* Logo */}
                <Link to="/productos" className="user-logo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z" />
                        <path d="M2 17l10 5 10-5" />
                        <path d="M2 12l10 5 10-5" />
                    </svg>
                    <span>Apotheclean</span>
                </Link>

                {/* Navegación (por ahora solo tienda) */}
                <nav className="user-nav">
                    <Link to="/productos" className="user-nav-link active">
                        Tienda
                    </Link>
                </nav>

                {/* Menú de usuario */}
                <div className="user-account">
                    <button
                        className="user-account-button"
                        onClick={() => setMenuAbierto(!menuAbierto)}
                        type="button"
                    >
                        Bienvenido a Apotheclean, {usuario?.nombre}
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="6 9 12 15 18 9" />
                        </svg>
                    </button>

                    {menuAbierto && (
                        <div className="user-account-menu">
                            <button
                                onClick={handleDeshabilitarCuenta}
                                className="user-account-menu-item text-danger"
                                type="button"
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                                </svg>
                                Deshabilitar cuenta
                            </button>
                            <button
                                onClick={handleLogout}
                                className="user-account-menu-item"
                                type="button"
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                    <polyline points="16 17 21 12 16 7" />
                                    <line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Cerrar sesión
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
