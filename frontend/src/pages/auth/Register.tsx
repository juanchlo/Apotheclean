/**
 * Página de Registro para usuarios clientes.
 * Solo usuarios clientes pueden registrarse desde el frontend.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registro } from '../../api/auth.api';
import { ApiException } from '../../api/client';
import './Register.css';

/**
 * Componente de página de registro.
 * Formulario para crear nueva cuenta de usuario cliente.
 */
export function Register() {
    const navigate = useNavigate();

    // Estado del formulario
    const [nombre, setNombre] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [exito, setExito] = useState(false);
    const [cargando, setCargando] = useState(false);

    /**
     * Maneja el envío del formulario de registro.
     */
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError(null);

        // Validar que las contraseñas coincidan
        if (password !== confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }

        // Validar longitud de contraseña
        if (password.length < 6) {
            setError('La contraseña debe tener al menos 6 caracteres');
            return;
        }

        setCargando(true);

        try {
            await registro({
                nombre,
                username,
                email,
                password,
            });

            setExito(true);

            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                navigate('/login');
            }, 2000);
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

    // Mostrar mensaje de éxito
    if (exito) {
        return (
            <div className="register-page">
                <div className="register-background">
                    <div className="register-background-shape register-background-shape-1" />
                    <div className="register-background-shape register-background-shape-2" />
                </div>

                <div className="register-card register-success">
                    <div className="success-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                        </svg>
                    </div>
                    <h2>¡Registro exitoso!</h2>
                    <p>Tu cuenta ha sido creada correctamente.</p>
                    <p className="redirect-message">Redirigiendo al login...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="register-page">
            {/* Fondo decorativo */}
            <div className="register-background">
                <div className="register-background-shape register-background-shape-1" />
                <div className="register-background-shape register-background-shape-2" />
            </div>

            {/* Card de registro */}
            <div className="register-card">
                {/* Header */}
                <div className="register-header">
                    <Link to="/login" className="register-back">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="19" y1="12" x2="5" y2="12" />
                            <polyline points="12 19 5 12 12 5" />
                        </svg>
                        Volver
                    </Link>
                    <h1 className="register-title">Crear Cuenta</h1>
                    <p className="register-subtitle">Únete a Apotheclean</p>
                </div>

                {/* Formulario */}
                <form className="register-form" onSubmit={handleSubmit}>
                    {/* Mensaje de error */}
                    {error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {/* Campo Nombre */}
                    <div className="input-group">
                        <label htmlFor="nombre" className="input-label">
                            Nombre completo
                        </label>
                        <input
                            id="nombre"
                            type="text"
                            className="input"
                            placeholder="Ej: Juan Pérez"
                            value={nombre}
                            onChange={(e) => setNombre(e.target.value)}
                            required
                            disabled={cargando}
                        />
                    </div>

                    {/* Campo Username */}
                    <div className="input-group">
                        <label htmlFor="username" className="input-label">
                            Nombre de usuario
                        </label>
                        <input
                            id="username"
                            type="text"
                            className="input"
                            placeholder="Ej: juanperez"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="username"
                        />
                    </div>

                    {/* Campo Email */}
                    <div className="input-group">
                        <label htmlFor="email" className="input-label">
                            Correo electrónico
                        </label>
                        <input
                            id="email"
                            type="email"
                            className="input"
                            placeholder="Ej: juan@ejemplo.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="email"
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
                            className="input"
                            placeholder="Mínimo 6 caracteres"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="new-password"
                        />
                    </div>

                    {/* Campo Confirmar Password */}
                    <div className="input-group">
                        <label htmlFor="confirmPassword" className="input-label">
                            Confirmar contraseña
                        </label>
                        <input
                            id="confirmPassword"
                            type="password"
                            className="input"
                            placeholder="Repita su contraseña"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            disabled={cargando}
                            autoComplete="new-password"
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
                                Registrando...
                            </>
                        ) : (
                            'Crear cuenta'
                        )}
                    </button>
                </form>

                {/* Footer */}
                <div className="register-footer">
                    <p>
                        ¿Ya tienes cuenta?{' '}
                        <Link to="/login">Inicia sesión</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
