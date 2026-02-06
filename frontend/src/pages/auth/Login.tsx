/**
 * Página de Login para Apotheclean.
 * Permite seleccionar entre modo Usuario o Administrador.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login, type Usuario } from '../../api/auth.api';
import { ApiException } from '../../api/client';
import './Login.css';

/** Tipo de usuario seleccionado */
type TipoUsuario = 'usuario' | 'admin';

/**
 * Componente de página de login.
 * Muestra tabs para seleccionar tipo de acceso y formulario de credenciales.
 */
export function Login() {
    const navigate = useNavigate();

    // Estado del formulario
    const [tipoUsuario, setTipoUsuario] = useState<TipoUsuario>('usuario');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [cargando, setCargando] = useState(false);

    /**
     * Maneja el envío del formulario de login.
     */
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);
        setCargando(true);

        try {
            const usuario: Usuario = await login({
                username,
                password,
            });

            // Validar rol según tipo seleccionado
            if (tipoUsuario === 'admin' && usuario.rol !== 'admin') {
                setError('Esta cuenta no tiene permisos de administrador');
                setCargando(false);
                return;
            }

            // Redirigir según rol
            if (usuario.rol === 'admin') {
                navigate('/admin/reportes');
            } else {
                navigate('/productos');
            }
        } catch (err) {
            if (err instanceof ApiException) {
                setError(err.message);
            } else {
                setError('Error de conexión. Intente nuevamente.');
            }
        } finally {
            setCargando(false);
        }
    };

    return (
        <div className="login-page">
            {/* Fondo decorativo */}
            <div className="login-background">
                <div className="login-background-shape login-background-shape-1" />
                <div className="login-background-shape login-background-shape-2" />
            </div>

            {/* Card de login */}
            <div className="login-card">
                {/* Logo y título */}
                <div className="login-header">
                    <div className="login-logo">
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="login-logo-icon"
                        >
                            <path d="M12 2L2 7l10 5 10-5-10-5z" />
                            <path d="M2 17l10 5 10-5" />
                            <path d="M2 12l10 5 10-5" />
                        </svg>
                    </div>
                    <h1 className="login-title">Apotheclean</h1>
                    <p className="login-subtitle">Sistema de Gestión de Farmacia</p>
                </div>

                {/* Selector de tipo de usuario */}
                <div className="login-tabs">
                    <button
                        type="button"
                        className={`login-tab ${tipoUsuario === 'usuario' ? 'login-tab-active' : ''}`}
                        onClick={() => setTipoUsuario('usuario')}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                        </svg>
                        Usuario
                    </button>
                    <button
                        type="button"
                        className={`login-tab ${tipoUsuario === 'admin' ? 'login-tab-active' : ''}`}
                        onClick={() => setTipoUsuario('admin')}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 15v2m-6 4h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2zm10-10V7a4 4 0 0 0-8 0v4h8z" />
                        </svg>
                        Administrador
                    </button>
                </div>

                {/* Formulario */}
                <form className="login-form" onSubmit={handleSubmit}>
                    {/* Mensaje de error */}
                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {/* Campo Username */}
                    <div className="input-group">
                        <label htmlFor="username" className="input-label">
                            Nombre de usuario
                        </label>
                        <input
                            id="username"
                            type="text"
                            className={`input ${error ? 'input-error' : ''}`}
                            placeholder="Ingrese su usuario"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="username"
                        />
                    </div>

                    {/* Campo Password */}
                    <div className="input-group">
                        <label htmlFor="password" className="input-label">
                            Contraseña
                        </label>
                        <input
                            id="password"
                            type="password"
                            className={`input ${error ? 'input-error' : ''}`}
                            placeholder="Ingrese su contraseña"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="current-password"
                        />
                    </div>

                    {/* Botón de submit */}
                    <button
                        type="submit"
                        className="btn btn-primary btn-lg btn-full"
                        disabled={cargando}
                    >
                        {cargando ? (
                            <>
                                <span className="loading-spinner" />
                                Iniciando sesión...
                            </>
                        ) : (
                            `Ingresar como ${tipoUsuario === 'admin' ? 'Administrador' : 'Usuario'}`
                        )}
                    </button>
                </form>

                {/* Link a registro (solo para usuarios) */}
                {tipoUsuario === 'usuario' && (
                    <div className="login-footer">
                        <p>
                            ¿No tienes cuenta?{' '}
                            <Link to="/registro">Regístrate aquí</Link>
                        </p>
                    </div>
                )}

                {/* Nota para administradores */}
                {tipoUsuario === 'admin' && (
                    <div className="login-footer login-footer-admin">
                        <p>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="16" x2="12" y2="12" />
                                <line x1="12" y1="8" x2="12.01" y2="8" />
                            </svg>
                            Las cuentas de administrador son creadas internamente
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
