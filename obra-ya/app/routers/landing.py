"""
Landing page de ObraYa — pagina principal publica.
Diseno basado en Style Guide: Paleta A (Dark Navy + Naranja Obra).
Agente NICO. Copy que vende.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter(tags=["landing"])


@router.get("/auth/config")
def auth_config():
    """Client IDs publicos para OAuth (no son secretos)."""
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "microsoft_client_id": settings.MICROSOFT_CLIENT_ID,
    }


@router.get("/", response_class=HTMLResponse)
def landing_page():
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ObraYa — Deja de perder horas cotizando materiales</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', system-ui, sans-serif; background: #FAFAF8; color: #1a1a1a; -webkit-font-smoothing: antialiased; }

        /* === COLORS === */
        :root {
            --navy: #0F1B2D;
            --navy-mid: #1a3a5c;
            --orange: #E67E22;
            --orange-hover: #D35400;
            --blue: #2E86C1;
            --green: #27AE60;
            --cream: #FAFAF8;
            --gray-bg: #F5F5F0;
        }

        /* === UTILITIES === */
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        .pill { border-radius: 100px; }
        .accent { color: var(--orange); }

        /* === NAV === */
        nav {
            position: fixed; top: 0; left: 0; right: 0; z-index: 100;
            padding: 16px 40px;
            background: rgba(15,27,45,0.92); backdrop-filter: blur(16px);
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .nav-brand { color: var(--orange); font-weight: 900; font-size: 20px; letter-spacing: -0.5px; text-decoration: none; }
        .nav-links { display: flex; gap: 28px; align-items: center; }
        .nav-links a { color: rgba(255,255,255,0.6); text-decoration: none; font-size: 13px; font-weight: 500; letter-spacing: 0.3px; transition: color 0.2s; }
        .nav-links a:hover { color: #fff; }
        .nav-cta {
            background: var(--orange); color: #fff !important; padding: 8px 20px;
            border-radius: 100px; font-weight: 600; font-size: 13px; transition: all 0.2s;
        }
        .nav-cta:hover { background: var(--orange-hover); transform: translateY(-1px); }

        /* === HERO === */
        .hero {
            min-height: 100vh; display: flex; align-items: center;
            background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 40%, #1e4d7a 100%);
            position: relative; overflow: hidden; padding-top: 80px;
        }
        .hero::before {
            content: ''; position: absolute; top: -40%; right: -15%;
            width: 700px; height: 700px;
            background: radial-gradient(circle, rgba(230,126,34,0.12) 0%, transparent 70%);
        }
        .hero::after {
            content: ''; position: absolute; bottom: -30%; left: -10%;
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(46,134,193,0.15) 0%, transparent 70%);
        }
        .hero-inner {
            position: relative; z-index: 2;
            display: flex; align-items: center; gap: 56px; width: 100%;
        }
        .hero-text { flex: 1; color: #fff; }
        .hero-badge {
            display: inline-block; padding: 6px 18px;
            background: rgba(230,126,34,0.15); border: 1px solid rgba(230,126,34,0.35);
            border-radius: 100px; font-size: 12px; font-weight: 600;
            letter-spacing: 0.5px; color: var(--orange); margin-bottom: 28px;
        }
        .hero h1 {
            font-size: clamp(38px, 5vw, 62px); font-weight: 800;
            line-height: 1.06; letter-spacing: -2.5px; margin-bottom: 20px;
        }
        .hero-sub {
            font-size: 18px; line-height: 1.65; color: rgba(255,255,255,0.7);
            max-width: 520px; margin-bottom: 36px;
        }
        .hero-buttons { display: flex; gap: 14px; flex-wrap: wrap; }
        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 15px 32px; border-radius: 100px; font-size: 15px;
            font-weight: 600; text-decoration: none; border: none; cursor: pointer;
            transition: all 0.25s; font-family: 'Inter', sans-serif;
        }
        .btn-orange { background: var(--orange); color: #fff; }
        .btn-orange:hover { background: var(--orange-hover); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(230,126,34,0.4); }
        .btn-ghost-white { background: transparent; color: #fff; border: 2px solid rgba(255,255,255,0.2); }
        .btn-ghost-white:hover { border-color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.05); }
        .btn-wa { background: #25D366; color: #fff; }
        .btn-wa:hover { background: #1fb855; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(37,211,102,0.35); }
        .btn-dark { background: var(--navy); color: #fff; }
        .btn-dark:hover { background: var(--navy-mid); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(15,27,45,0.4); }

        .hero-metrics {
            display: flex; gap: 36px; margin-top: 52px; padding-top: 32px;
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        .metric-num { font-size: 34px; font-weight: 800; letter-spacing: -1px; color: #fff; }
        .metric-num span { font-size: 18px; font-weight: 500; }
        .metric-label { font-size: 13px; color: rgba(255,255,255,0.45); margin-top: 2px; font-weight: 500; }

        /* === WHATSAPP MOCKUP (HERO) === */
        .wa-mock {
            width: 370px; flex-shrink: 0;
            background: #fff; border-radius: 20px; overflow: hidden;
            box-shadow: 0 25px 80px rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.1);
            transform: perspective(800px) rotateY(-2deg) rotateX(1deg);
            transition: transform 0.4s;
        }
        .wa-mock:hover { transform: perspective(800px) rotateY(0deg) rotateX(0deg) translateY(-4px); }
        .wa-head { background: #075E54; padding: 12px 16px; color: #fff; display: flex; align-items: center; gap: 12px; }
        .wa-avatar {
            width: 36px; height: 36px; border-radius: 50%; background: var(--orange);
            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px;
        }
        .wa-name { font-size: 15px; font-weight: 600; }
        .wa-status { font-size: 11px; opacity: 0.7; }
        .wa-body { background: #ECE5DD; padding: 14px; display: flex; flex-direction: column; gap: 6px; min-height: 310px; }
        .wa-msg {
            padding: 8px 12px; border-radius: 8px; font-size: 13px;
            line-height: 1.45; max-width: 88%; position: relative; color: #111;
        }
        .wa-msg-time { font-size: 10px; color: #999; text-align: right; margin-top: 3px; }
        .wa-user { background: #DCF8C6; align-self: flex-end; border-bottom-right-radius: 2px; }
        .wa-bot { background: #fff; align-self: flex-start; border-bottom-left-radius: 2px; }
        .wa-bot strong { color: var(--orange); }
        .wa-input {
            padding: 8px 14px; background: #f0f0f0; display: flex; align-items: center; gap: 8px;
        }
        .wa-input-field {
            flex: 1; padding: 10px 16px; border-radius: 20px; border: none;
            background: #fff; font-size: 13px; font-family: 'Inter'; color: #333;
        }

        /* === PAIN SECTION === */
        .pain {
            padding: 100px 24px; background: var(--cream);
        }
        .pain-inner { max-width: 900px; margin: 0 auto; text-align: center; }
        .pain h2 {
            font-size: clamp(28px, 3.5vw, 42px); font-weight: 800;
            letter-spacing: -1.5px; color: var(--navy); margin-bottom: 20px; line-height: 1.15;
        }
        .pain-sub { font-size: 17px; line-height: 1.65; color: #666; max-width: 640px; margin: 0 auto 48px; }
        .pain-compare {
            display: grid; grid-template-columns: 1fr auto 1fr; gap: 24px;
            align-items: center; max-width: 800px; margin: 0 auto;
        }
        .pain-card {
            background: #fff; border-radius: 20px; padding: 36px 28px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.04);
            text-align: left;
        }
        .pain-card.old { border-top: 4px solid #e74c3c; }
        .pain-card.new { border-top: 4px solid var(--green); }
        .pain-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; }
        .pain-card.old h3 { color: #e74c3c; }
        .pain-card.new h3 { color: var(--green); }
        .pain-item {
            display: flex; align-items: flex-start; gap: 10px;
            font-size: 14px; line-height: 1.5; color: #555; margin-bottom: 12px;
        }
        .pain-item .icon { flex-shrink: 0; font-size: 16px; margin-top: 1px; }
        .pain-vs {
            font-size: 20px; font-weight: 800; color: var(--navy);
            background: var(--gray-bg); width: 48px; height: 48px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
        }

        /* === COMO FUNCIONA === */
        .steps { padding: 100px 24px; background: #fff; }
        .section-tag {
            display: inline-block; padding: 5px 14px; background: rgba(230,126,34,0.1);
            border-radius: 100px; font-size: 12px; font-weight: 700;
            color: var(--orange); letter-spacing: 0.5px; margin-bottom: 16px;
        }
        .section-title {
            font-size: clamp(28px, 3.5vw, 42px); font-weight: 800;
            letter-spacing: -1.5px; color: var(--navy); margin-bottom: 12px; line-height: 1.15;
        }
        .section-sub { font-size: 16px; color: #888; margin-bottom: 56px; }
        .steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .step-card {
            background: var(--cream); border-radius: 20px; padding: 36px 28px;
            border: 1px solid rgba(0,0,0,0.04); transition: all 0.3s; position: relative;
        }
        .step-card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.08); }
        .step-num {
            font-size: 52px; font-weight: 900; letter-spacing: -3px;
            color: rgba(230,126,34,0.12); margin-bottom: 16px; line-height: 1;
        }
        .step-icon {
            width: 48px; height: 48px; border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; margin-bottom: 20px;
        }
        .step-card h3 { font-size: 19px; font-weight: 700; color: var(--navy); margin-bottom: 10px; }
        .step-card p { font-size: 14px; line-height: 1.6; color: #666; }
        .step-example {
            margin-top: 16px; padding: 12px 14px; background: #fff;
            border-radius: 12px; font-size: 13px; color: #888;
            border-left: 3px solid var(--orange); font-style: italic;
        }

        /* === NICO (AGENT) === */
        .fierro {
            padding: 100px 24px;
            background: var(--navy);
            color: #fff; position: relative; overflow: hidden;
        }
        .fierro::before {
            content: ''; position: absolute; top: -20%; right: -10%;
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(230,126,34,0.08) 0%, transparent 70%);
        }
        .fierro-inner {
            max-width: 1200px; margin: 0 auto;
            display: flex; gap: 56px; align-items: center; position: relative; z-index: 2;
        }
        .fierro-info { flex: 1; }
        .fierro-badge {
            display: inline-block; padding: 5px 14px;
            background: rgba(230,126,34,0.2); border-radius: 8px;
            font-size: 11px; font-weight: 700; color: var(--orange);
            letter-spacing: 1px; text-transform: uppercase; margin-bottom: 20px;
        }
        .fierro-name {
            font-size: clamp(40px, 4vw, 56px); font-weight: 900;
            letter-spacing: -2px; margin-bottom: 20px; line-height: 1.05;
        }
        .fierro-desc { font-size: 17px; line-height: 1.7; color: rgba(255,255,255,0.6); margin-bottom: 32px; max-width: 500px; }
        .fierro-features { display: flex; flex-direction: column; gap: 14px; margin-bottom: 36px; }
        .fierro-feat {
            display: flex; align-items: center; gap: 12px;
            font-size: 14px; font-weight: 500; color: rgba(255,255,255,0.8);
        }
        .fierro-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--orange); flex-shrink: 0; }

        /* === SOCIAL PROOF / NUMBERS === */
        .proof {
            padding: 80px 24px; background: var(--gray-bg);
        }
        .proof-grid {
            max-width: 1000px; margin: 0 auto;
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
        }
        .proof-card {
            text-align: center; padding: 32px 20px; background: #fff;
            border-radius: 20px; box-shadow: 0 1px 8px rgba(0,0,0,0.03);
        }
        .proof-num { font-size: 40px; font-weight: 800; letter-spacing: -2px; margin-bottom: 6px; }
        .proof-label { font-size: 13px; color: #888; font-weight: 500; }

        /* === MATERIALS === */
        .materials { padding: 100px 24px; background: #fff; }
        .mat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; }
        .mat-card {
            background: var(--cream); border-radius: 16px; padding: 24px 16px;
            text-align: center; border: 1px solid rgba(0,0,0,0.03);
            transition: all 0.2s; cursor: default;
        }
        .mat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); border-color: rgba(230,126,34,0.2); }
        .mat-icon { font-size: 28px; margin-bottom: 10px; }
        .mat-name { font-size: 14px; font-weight: 700; color: var(--navy); margin-bottom: 2px; }
        .mat-detail { font-size: 11px; color: #999; }

        /* === PRICES === */
        .prices { padding: 100px 24px; background: var(--navy); color: #fff; }
        .prices-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 900px; margin: 0 auto; }
        .price-card {
            background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
            border-radius: 20px; padding: 32px 24px; transition: all 0.3s;
        }
        .price-card:hover { background: rgba(255,255,255,0.08); transform: translateY(-4px); }
        .price-tag { font-size: 13px; font-weight: 600; margin-bottom: 12px; }
        .price-num { font-size: 36px; font-weight: 800; letter-spacing: -1px; }
        .price-num span { font-size: 16px; font-weight: 500; color: rgba(255,255,255,0.5); }
        .price-detail { font-size: 13px; color: rgba(255,255,255,0.4); margin-top: 6px; }

        /* === CTA === */
        .cta {
            padding: 100px 24px; text-align: center;
            background: linear-gradient(135deg, var(--orange) 0%, var(--orange-hover) 100%);
            color: #fff; position: relative; overflow: hidden;
        }
        .cta::before {
            content: ''; position: absolute; inset: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
        .cta-inner { position: relative; z-index: 2; max-width: 600px; margin: 0 auto; }
        .cta h2 {
            font-size: clamp(30px, 4vw, 48px); font-weight: 800;
            letter-spacing: -1.5px; margin-bottom: 16px; line-height: 1.1;
        }
        .cta p { font-size: 18px; line-height: 1.6; color: rgba(255,255,255,0.85); margin-bottom: 36px; }
        .cta-buttons { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

        /* === FOOTER === */
        footer {
            background: var(--navy); color: rgba(255,255,255,0.4); padding: 48px 24px;
            text-align: center; font-size: 13px; border-top: 1px solid rgba(255,255,255,0.05);
        }
        footer .brand { color: var(--orange); font-weight: 800; font-size: 18px; margin-bottom: 8px; }
        footer a { color: rgba(255,255,255,0.5); text-decoration: none; }
        footer a:hover { color: #fff; }
        .footer-links { display: flex; gap: 24px; justify-content: center; margin-top: 20px; }

        /* === ANIMATIONS === */
        .fade-up { opacity: 0; transform: translateY(30px); transition: all 0.7s ease; }
        .fade-up.visible { opacity: 1; transform: translateY(0); }
        .slide-right { opacity: 0; transform: translateX(-30px); transition: all 0.7s ease; }
        .slide-right.visible { opacity: 1; transform: translateX(0); }

        /* === AUTH MODAL === */
        .auth-overlay {
            display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
            z-index: 1000; justify-content: center; align-items: center;
        }
        .auth-overlay.open { display: flex; }
        .auth-modal {
            background: #fff; border-radius: 20px; width: 440px; max-width: 94vw;
            max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 80px rgba(0,0,0,0.3);
            position: relative; animation: modalIn 0.3s ease;
        }
        @keyframes modalIn { from { opacity:0; transform:translateY(20px) scale(0.97); } to { opacity:1; transform:translateY(0) scale(1); } }
        .auth-modal-header {
            padding: 32px 32px 0; text-align: center;
        }
        .auth-modal-header h2 { font-size: 22px; color: var(--navy); font-weight: 800; }
        .auth-modal-header p { font-size: 14px; color: #666; margin-top: 6px; }
        .auth-close {
            position: absolute; top: 16px; right: 16px; background: none; border: none;
            font-size: 22px; color: #999; cursor: pointer; width: 36px; height: 36px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            transition: all 0.2s;
        }
        .auth-close:hover { background: #f0f0f0; color: #333; }
        .auth-body { padding: 24px 32px 32px; }

        /* Tabs: Iniciar sesion / Crear cuenta */
        .auth-tabs {
            display: flex; gap: 0; margin-bottom: 24px; background: #f5f5f0;
            border-radius: 12px; padding: 4px; overflow: hidden;
        }
        .auth-tab {
            flex: 1; padding: 10px 16px; text-align: center; font-size: 13px; font-weight: 600;
            color: #666; cursor: pointer; border-radius: 10px; border: none; background: none;
            transition: all 0.2s;
        }
        .auth-tab.active { background: #fff; color: var(--navy); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

        /* OAuth buttons */
        .oauth-buttons { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        .oauth-btn {
            display: flex; align-items: center; justify-content: center; gap: 10px;
            padding: 12px 16px; border-radius: 12px; font-size: 14px; font-weight: 600;
            cursor: pointer; transition: all 0.2s; border: 1.5px solid #e0e0e0;
            background: #fff; color: #333; width: 100%;
        }
        .oauth-btn:hover { border-color: #bbb; background: #fafafa; transform: translateY(-1px); }
        .oauth-btn svg { width: 20px; height: 20px; flex-shrink: 0; }

        .auth-divider {
            display: flex; align-items: center; gap: 12px; margin: 20px 0;
            font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 1px;
        }
        .auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #e5e5e5; }

        /* Form fields */
        .auth-field { margin-bottom: 14px; }
        .auth-field label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
        .auth-field input, .auth-field select {
            width: 100%; padding: 12px 14px; border: 1.5px solid #e0e0e0; border-radius: 10px;
            font-size: 14px; font-family: inherit; transition: border-color 0.2s; background: #fff;
        }
        .auth-field input:focus, .auth-field select:focus { outline: none; border-color: var(--orange); }

        /* Phone with country code */
        .phone-row { display: flex; gap: 8px; }
        .phone-country {
            width: 120px; flex-shrink: 0; padding: 12px 8px; border: 1.5px solid #e0e0e0;
            border-radius: 10px; font-size: 13px; font-family: inherit; background: #fff;
            cursor: pointer;
        }
        .phone-country:focus { outline: none; border-color: var(--orange); }
        .phone-input {
            flex: 1; min-width: 0; padding: 12px 14px; border: 1.5px solid #e0e0e0;
            border-radius: 10px; font-size: 15px; font-family: inherit;
        }
        .phone-input:focus { outline: none; border-color: var(--orange); }

        /* Role selector */
        .role-selector { display: flex; gap: 8px; margin-bottom: 14px; }
        .role-btn {
            flex: 1; padding: 12px 16px; border-radius: 12px; border: 1.5px solid #e0e0e0;
            background: #fff; cursor: pointer; text-align: center; transition: all 0.2s;
        }
        .role-btn:hover { border-color: #bbb; }
        .role-btn.active { border-color: var(--orange); background: #FFF5EB; }
        .role-btn .role-icon { font-size: 24px; display: block; margin-bottom: 4px; }
        .role-btn .role-label { font-size: 12px; font-weight: 600; color: #333; }
        .role-btn .role-desc { font-size: 11px; color: #888; margin-top: 2px; }

        /* Submit */
        .auth-submit {
            width: 100%; padding: 14px; border: none; border-radius: 12px;
            background: var(--orange); color: #fff; font-size: 15px; font-weight: 700;
            cursor: pointer; transition: all 0.2s; margin-top: 8px;
        }
        .auth-submit:hover { background: var(--orange-hover); transform: translateY(-1px); }
        .auth-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .auth-error { color: #e74c3c; font-size: 13px; text-align: center; margin-top: 10px; display: none; }
        .auth-success { color: var(--green); font-size: 13px; text-align: center; margin-top: 10px; display: none; }

        /* User menu (when logged in) */
        .user-menu { display: flex; align-items: center; gap: 10px; }
        .user-avatar {
            width: 32px; height: 32px; border-radius: 50%; background: var(--orange);
            color: #fff; display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 13px; overflow: hidden;
        }
        .user-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .user-name { color: rgba(255,255,255,0.8); font-size: 13px; font-weight: 500; }

        /* === HAMBURGER MENU === */
        .hamburger {
            display: none; background: none; border: none; cursor: pointer;
            padding: 8px; z-index: 200; position: relative;
        }
        .hamburger span {
            display: block; width: 24px; height: 2px; background: #fff;
            margin: 6px 0; border-radius: 2px; transition: all 0.3s;
        }
        .hamburger.active span:nth-child(1) { transform: rotate(45deg) translate(5px, 6px); }
        .hamburger.active span:nth-child(2) { opacity: 0; }
        .hamburger.active span:nth-child(3) { transform: rotate(-45deg) translate(5px, -6px); }

        /* === RESPONSIVE === */
        @media (max-width: 900px) {
            /* Nav: hamburger menu */
            .hamburger { display: block; }
            .nav-links {
                display: none; flex-direction: column; position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15,27,45,0.98); backdrop-filter: blur(20px);
                justify-content: center; align-items: center;
                gap: 28px; z-index: 150;
            }
            .nav-links.open { display: flex; }
            .nav-links a { font-size: 18px; color: rgba(255,255,255,0.8); }
            .nav-cta { padding: 14px 32px; font-size: 16px; }
            nav { padding: 12px 20px; }

            /* Hero: stack vertically */
            .hero-inner { flex-direction: column; text-align: center; padding: 40px 0; }
            .hero-sub { margin-left: auto; margin-right: auto; }
            .hero-buttons { justify-content: center; }
            .hero-metrics { justify-content: center; flex-wrap: wrap; gap: 24px; }
            .wa-mock { width: 340px; max-width: 100%; transform: none; }

            /* Pain: stack cards */
            .pain-compare { grid-template-columns: 1fr; }
            .pain-vs { margin: 0 auto; }

            /* Steps: stack */
            .steps-grid { grid-template-columns: 1fr; }

            /* Nico: stack */
            .fierro-inner { flex-direction: column; text-align: center; }
            .fierro-desc { margin-left: auto; margin-right: auto; }
            .fierro-features { align-items: center; }
            .fierro .wa-mock { width: 340px; max-width: 100%; }

            /* Proof: 2 cols */
            .proof-grid { grid-template-columns: repeat(2, 1fr); }

            /* Materials: fewer cols */
            .mat-grid { grid-template-columns: repeat(3, 1fr); }

            /* Prices: stack */
            .prices-grid { grid-template-columns: 1fr; max-width: 400px; }

            /* CTA: tighter padding */
            .cta { padding: 72px 20px; }
            .cta-buttons { flex-direction: column; align-items: center; }

            /* Footer: wrap links */
            .footer-links { flex-wrap: wrap; gap: 16px; }
        }

        @media (max-width: 600px) {
            /* Typography: ensure readability */
            body { font-size: 15px; }
            .hero h1 { letter-spacing: -1.5px; }
            .hero-sub { font-size: 16px; }
            .pain-sub { font-size: 15px; }
            .pain-item { font-size: 14px; }
            .step-card p { font-size: 14px; }
            .fierro-desc { font-size: 15px; }
            .section-sub { font-size: 14px; }

            /* Touch-friendly buttons: min 44px height */
            .btn { padding: 14px 28px; font-size: 15px; min-height: 44px; }
            .nav-cta { min-height: 44px; }

            /* WhatsApp mockups: fit small screens */
            .wa-mock { width: 100%; max-width: 340px; }

            /* Proof grid stays 2 cols */
            .proof-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
            .proof-num { font-size: 30px; }
            .proof-card { padding: 20px 12px; }

            /* Materials: 2 cols on small screens */
            .mat-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }

            /* Hero metrics: 2 cols */
            .hero-metrics { gap: 16px; }
            .metric-num { font-size: 26px; }

            /* Sections: tighter padding */
            .pain { padding: 64px 16px; }
            .steps { padding: 64px 16px; }
            .fierro { padding: 64px 16px; }
            .platform { padding: 64px 16px; }
            .platform-grid { grid-template-columns: 1fr; }
            .materials { padding: 64px 16px; }
            .prices { padding: 64px 16px; }
            .proof { padding: 48px 16px; }
            .cta { padding: 56px 16px; }
            footer { padding: 36px 16px; }

            /* Footer links wrap */
            .footer-links { flex-wrap: wrap; gap: 12px; justify-content: center; }
            .footer-links a { font-size: 14px; padding: 4px 0; }

            /* Pain cards: less padding */
            .pain-card { padding: 24px 20px; }
            .step-card { padding: 28px 20px; }

            /* Platform: stack */
            .platform { padding: 64px 16px; }
            .platform-grid { grid-template-columns: 1fr; }
        }

        /* === PLATAFORMA COMPLETA === */
        .platform {
            padding: 100px 24px; background: var(--cream);
        }
        .platform-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
            max-width: 1100px; margin: 0 auto;
        }
        .platform-card {
            background: #fff; border-radius: 20px; padding: 36px 28px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.04);
            text-align: left; transition: all 0.3s; position: relative; overflow: hidden;
        }
        .platform-card::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
        }
        .platform-card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.08); }
        .platform-card .card-num {
            display: flex; align-items: center; justify-content: center;
            width: 44px; height: 44px; border-radius: 12px;
            font-size: 18px; font-weight: 800; margin-bottom: 20px; color: #fff;
        }
        .platform-card h3 { font-size: 18px; font-weight: 700; color: var(--navy); margin-bottom: 10px; }
        .platform-card p { font-size: 14px; line-height: 1.65; color: #666; }
        .platform-card:nth-child(1)::before { background: var(--blue); }
        .platform-card:nth-child(1) .card-num { background: var(--blue); }
        .platform-card:nth-child(2)::before { background: var(--orange); }
        .platform-card:nth-child(2) .card-num { background: var(--orange); }
        .platform-card:nth-child(3)::before { background: var(--green); }
        .platform-card:nth-child(3) .card-num { background: var(--green); }
        .platform-card:nth-child(4)::before { background: var(--navy); }
        .platform-card:nth-child(4) .card-num { background: var(--navy); }
        .platform-card:nth-child(5)::before { background: var(--orange); }
        .platform-card:nth-child(5) .card-num { background: var(--orange); }
        .platform-card:nth-child(6)::before { background: var(--blue); }
        .platform-card:nth-child(6) .card-num { background: var(--blue); }

        @media (max-width: 900px) {
            .platform-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<!-- NAV -->
<nav>
    <a href="/" class="nav-brand">ObraYa</a>
    <button class="hamburger" id="hamburger" aria-label="Menu">
        <span></span><span></span><span></span>
    </button>
    <div class="nav-links" id="nav-links">
        <a href="#como-funciona">Como funciona</a>
        <a href="#fierro">El Agente</a>
        <a href="#plataforma">Plataforma</a>
        <a href="#precios">Precios</a>
        <a href="#" data-auth="login" id="nav-login-btn" style="color:rgba(255,255,255,0.85); font-weight:600;">Iniciar sesion</a>
        <a href="#" data-auth="register" id="nav-register-btn" class="nav-cta">Crear cuenta</a>
        <!-- Visible when logged in -->
        <div class="user-menu" id="nav-user-menu" style="display:none;">
            <div class="user-avatar" id="nav-user-avatar"></div>
            <a href="/portal/" class="nav-cta" style="font-size:12px;">Mi Portal</a>
        </div>
    </div>
</nav>

<!-- ============ AUTH MODAL ============ -->
<div class="auth-overlay" id="auth-overlay" onclick="if(event.target===this) closeAuth()">
    <div class="auth-modal">
        <button class="auth-close" onclick="closeAuth()">&times;</button>
        <div class="auth-modal-header">
            <h2 id="auth-title">Iniciar sesion</h2>
            <p id="auth-subtitle">Accede a tu cuenta de ObraYa</p>
        </div>
        <div class="auth-body">
            <!-- Tabs -->
            <div class="auth-tabs">
                <button class="auth-tab active" onclick="switchAuthTab('login')">Iniciar sesion</button>
                <button class="auth-tab" onclick="switchAuthTab('register')">Crear cuenta</button>
            </div>

            <!-- OAuth buttons -->
            <div class="oauth-buttons">
                <div id="google-signin-btn" style="display:flex;justify-content:center;"></div>
            </div>

            <div class="auth-divider">o</div>

            <!-- Login form (default visible) -->
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="auth-field">
                    <label>Correo electronico</label>
                    <input type="email" id="login-email" placeholder="tu@empresa.com" required>
                </div>
                <div class="auth-field">
                    <label>Contrasena</label>
                    <input type="password" id="login-password" placeholder="Tu contrasena" required>
                </div>
                <button type="submit" class="auth-submit" id="login-btn">Iniciar sesion</button>
            </form>

            <!-- Register form (hidden by default) -->
            <form id="register-form" style="display:none;" onsubmit="handleRegister(event)">
                <!-- Rol selector -->
                <div style="margin-bottom:16px;">
                    <label style="display:block; font-size:12px; font-weight:600; color:#555; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.5px;">Tipo de cuenta</label>
                    <div class="role-selector">
                        <div class="role-btn active" onclick="selectRole('comprador')" id="role-comprador">
                            <span class="role-icon">&#128736;</span>
                            <span class="role-label">Comprador</span>
                            <span class="role-desc">Cotizo materiales</span>
                        </div>
                        <div class="role-btn" onclick="selectRole('proveedor')" id="role-proveedor">
                            <span class="role-icon">&#128666;</span>
                            <span class="role-label">Proveedor</span>
                            <span class="role-desc">Vendo materiales</span>
                        </div>
                    </div>
                </div>
                <input type="hidden" id="reg-role" value="comprador">
                <div class="auth-field">
                    <label>Nombre completo</label>
                    <input type="text" id="reg-nombre" placeholder="Juan Perez" required>
                </div>
                <div class="auth-field">
                    <label>Correo electronico</label>
                    <input type="email" id="reg-email" placeholder="tu@empresa.com" required>
                </div>
                <div class="auth-field">
                    <label>Contrasena</label>
                    <input type="password" id="reg-password" placeholder="Minimo 6 caracteres" required minlength="6">
                </div>
                <div class="auth-field">
                    <label>Empresa (opcional)</label>
                    <input type="text" id="reg-empresa" placeholder="Constructora ABC">
                </div>
                <div class="auth-field">
                    <label>Telefono</label>
                    <div class="phone-row">
                        <select class="phone-country" id="reg-country-code">
                            <option value="+52">&#127474;&#127485; +52</option>
                            <option value="+1">&#127482;&#127480; +1</option>
                            <option value="+57">&#127464;&#127476; +57</option>
                            <option value="+56">&#127464;&#127473; +56</option>
                            <option value="+54">&#127462;&#127479; +54</option>
                            <option value="+55">&#127463;&#127479; +55</option>
                            <option value="+51">&#127477;&#127466; +51</option>
                            <option value="+593">&#127466;&#127464; +593</option>
                            <option value="+58">&#127483;&#127466; +58</option>
                            <option value="+506">&#127464;&#127479; +506</option>
                            <option value="+502">&#127468;&#127481; +502</option>
                            <option value="+503">&#127480;&#127483; +503</option>
                            <option value="+504">&#127469;&#127475; +504</option>
                            <option value="+505">&#127475;&#127470; +505</option>
                            <option value="+507">&#127477;&#127462; +507</option>
                            <option value="+591">&#127463;&#127476; +591</option>
                            <option value="+595">&#127477;&#127486; +595</option>
                            <option value="+598">&#127482;&#127486; +598</option>
                            <option value="+34">&#127466;&#127480; +34</option>
                        </select>
                        <input type="tel" id="reg-telefono" placeholder="33 1234 5678" class="phone-input">
                    </div>
                </div>
                <button type="submit" class="auth-submit" id="register-btn">Crear cuenta</button>
            </form>

            <div class="auth-error" id="auth-error"></div>
            <div class="auth-success" id="auth-success"></div>
        </div>
    </div>
</div>

<!-- ============ HERO ============ -->
<section class="hero">
    <div class="container">
        <div class="hero-inner">
            <div class="hero-text">
                <div class="hero-badge">Potenciado por Inteligencia Artificial</div>
                <h1>Deja de perder<br>horas cotizando <span class="accent">materiales.</span></h1>
                <p class="hero-sub">
                    La plataforma completa para compras de obra. Cotiza por WhatsApp, paga con tarjeta,
                    controla tu presupuesto y aprueba pedidos &mdash;todo desde un solo lugar.
                </p>
                <div class="hero-buttons">
                    <a href="#" onclick="openAuth('register'); return false;" class="btn btn-orange">Crear cuenta gratis &rarr;</a>
                    <a href="#como-funciona" class="btn btn-ghost-white">Ver como funciona</a>
                </div>
                <div class="hero-metrics">
                    <div>
                        <div class="metric-num">5 <span>min</span></div>
                        <div class="metric-label">Tiempo de cotizacion</div>
                    </div>
                    <div>
                        <div class="metric-num">10+</div>
                        <div class="metric-label">Proveedores comparados</div>
                    </div>
                    <div>
                        <div class="metric-num">15<span>%</span></div>
                        <div class="metric-label">Ahorro promedio</div>
                    </div>
                    <div>
                        <div class="metric-num">24/7</div>
                        <div class="metric-label">Siempre disponible</div>
                    </div>
                </div>
            </div>

            <!-- WhatsApp Mockup -->
            <div class="wa-mock">
                <div class="wa-head">
                    <div class="wa-avatar">N</div>
                    <div>
                        <div class="wa-name">Nico &bull; ObraYa</div>
                        <div class="wa-status">en linea</div>
                    </div>
                </div>
                <div class="wa-body">
                    <div class="wa-msg wa-user">
                        Necesito 100 varillas del 3/8, 50 del medio, 3 viajes de grava y 50 bultos del gris. Entrega manana en la obra.
                        <div class="wa-msg-time">10:23 AM</div>
                    </div>
                    <div class="wa-msg wa-bot">
                        <strong>Nico:</strong> Listo, confirmo tu pedido:<br><br>
                        &#8226; 100 varillas 3/8" G42<br>
                        &#8226; 50 varillas 1/2" G42<br>
                        &#8226; 3 viajes grava 3/4" (~21m3)<br>
                        &#8226; 50 bultos cemento CPC 30R<br><br>
                        Cotizando con 6 proveedores...
                        <div class="wa-msg-time">10:23 AM</div>
                    </div>
                    <div class="wa-msg wa-bot" style="font-size:12px; color:#111;">
                        <strong style="color:var(--orange);">1. Aceros Rojos</strong> &mdash; <span style="font-weight:700;">$18,400</span><br>
                        <strong style="color:var(--blue);">2. CEMEX</strong> &mdash; <span style="font-weight:700;">$19,100</span><br>
                        <strong style="color:#555;">3. Holcim</strong> &mdash; <span style="font-weight:700;">$19,850</span><br><br>
                        <em style="color:#333;">&#191;Con cual le entramos?</em>
                        <div class="wa-msg-time">10:25 AM</div>
                    </div>
                </div>
                <div class="wa-input">
                    <input class="wa-input-field" placeholder="Escribe un mensaje..." disabled>
                    <svg style="width:20px;height:20px;color:#128C7E;" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============ PAIN POINT ============ -->
<section class="pain">
    <div class="pain-inner">
        <h2>Hoy cotizar materiales es un <span class="accent">infierno.</span></h2>
        <p class="pain-sub">
            Llamar proveedor por proveedor, esperar respuestas, comparar en Excel,
            perseguir precios que cambian a diario. Para un pedido grande puedes perder un dia entero.
        </p>
        <div class="pain-compare">
            <div class="pain-card old">
                <h3>&#10005; Sin ObraYa</h3>
                <div class="pain-item"><span class="icon">&mdash;</span> Llamas a 5+ proveedores uno por uno</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Esperas horas o dias por respuestas</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Comparas precios en un Excel a mano</div>
                <div class="pain-item"><span class="icon">&mdash;</span> No sabes si incluye flete o no</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Siempre queda la duda: &iquest;habra mejor precio?</div>
            </div>
            <div class="pain-vs">vs</div>
            <div class="pain-card new">
                <h3>&#10003; Con ObraYa</h3>
                <div class="pain-item"><span class="icon">&mdash;</span> Un mensaje de WhatsApp y listo</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Respuesta en menos de 5 minutos</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Comparativa automatica con flete incluido</div>
                <div class="pain-item"><span class="icon">&mdash;</span> El agente entiende jerga de obra</div>
                <div class="pain-item"><span class="icon">&mdash;</span> Siempre sabes que tienes el mejor precio</div>
            </div>
        </div>
    </div>
</section>

<!-- ============ COMO FUNCIONA ============ -->
<section class="steps" id="como-funciona">
    <div class="container" style="text-align:center;">
        <div class="section-tag">Asi de facil</div>
        <div class="section-title">3 pasos. Un mensaje. Listo.</div>
        <div class="section-sub">Desde tu WhatsApp, sin apps, sin registros, sin complicaciones.</div>

        <div class="steps-grid" style="text-align:left;">
            <div class="step-card">
                <div class="step-num">01</div>
                <div class="step-icon" style="background:rgba(230,126,34,0.1); color:var(--orange); font-weight:800;">1</div>
                <h3>Manda tu pedido</h3>
                <p>Escribe o manda un audio con lo que necesitas. Usa tu lenguaje normal de obra &mdash;Nico entiende todo.</p>
                <div class="step-example">"Manda 15 metros de concreto del 250 con bomba y 200 varillas del tres octavos"</div>
            </div>
            <div class="step-card">
                <div class="step-num">02</div>
                <div class="step-icon" style="background:rgba(46,134,193,0.1); color:var(--blue); font-weight:800;">2</div>
                <h3>Nico cotiza por ti</h3>
                <p>El agente interpreta tu pedido, identifica materiales exactos, y lanza cotizaciones a todos los proveedores con stock.</p>
                <div class="step-example">CEMEX, Holcim, acereras, materialistas, blockeras... todos al mismo tiempo</div>
            </div>
            <div class="step-card">
                <div class="step-num">03</div>
                <div class="step-icon" style="background:rgba(39,174,96,0.1); color:var(--green); font-weight:800;">3</div>
                <h3>Elige y compra</h3>
                <p>Recibes una tabla comparativa con precio, flete, tiempo de entrega y calificacion del proveedor. Tu decides.</p>
                <div class="step-example">Mejor precio &middot; Mejor calificado &middot; Flete incluido</div>
            </div>
        </div>
    </div>
</section>

<!-- ============ NICO — EL AGENTE ============ -->
<section class="fierro" id="fierro">
    <div class="fierro-inner">
        <div class="fierro-info">
            <div class="fierro-badge">Agente de IA</div>
            <div class="fierro-name">Conoce a<br><span style="color:var(--orange);">NICO.</span></div>
            <p class="fierro-desc">
                Tu comprador de materiales con inteligencia artificial.
                Nico habla como hablas en obra, cotiza con todos tus proveedores
                al mismo tiempo, y te entrega la mejor opcion en minutos. Nunca descansa.
            </p>
            <div class="fierro-features">
                <div class="fierro-feat"><span class="fierro-dot"></span> Entiende "bultos del gris", "varilla del 3/8", "un viaje de grava"</div>
                <div class="fierro-feat"><span class="fierro-dot"></span> Cotiza con 10+ proveedores en simultaneo</div>
                <div class="fierro-feat"><span class="fierro-dot"></span> Calcula precio + flete + tiempo de entrega</div>
                <div class="fierro-feat"><span class="fierro-dot"></span> Aprende que proveedores cumplen y cuales no</div>
                <div class="fierro-feat"><span class="fierro-dot"></span> Acepta texto y mensajes de voz</div>
                <div class="fierro-feat"><span class="fierro-dot"></span> Disponible 24/7 por WhatsApp</div>
            </div>
            <a href="/sim/" class="btn btn-orange">Hablar con Nico &rarr;</a>
        </div>

        <!-- Mini WhatsApp -->
        <div class="wa-mock" style="transform:none; width:400px;">
            <div class="wa-head">
                <div class="wa-avatar">N</div>
                <div>
                    <div class="wa-name">Nico &bull; ObraYa</div>
                    <div class="wa-status">en linea</div>
                </div>
            </div>
            <div class="wa-body" style="min-height:260px;">
                <div class="wa-msg wa-user">
                    Nico, manda 3 ollas de concreto del 250 con bomba para manana a las 7
                    <div class="wa-msg-time">8:14 AM</div>
                </div>
                <div class="wa-msg wa-bot">
                    <span style="color:#333;">Va que va. 3 opciones listas:</span><br><br>
                    <strong style="color:var(--orange);">1. Concretera del Valle</strong><br>
                    <span style="color:#555;">21m3 f'c 250 bombeable</span><br>
                    <span style="color:#111; font-weight:700; font-size:14px;">$48,720</span> <span style="color:#888; font-size:11px;">flete incluido</span><br><br>
                    <strong style="color:var(--blue);">2. CEMEX</strong><br>
                    <span style="color:#555;">21m3 f'c 250 bombeable</span><br>
                    <span style="color:#111; font-weight:700; font-size:14px;">$51,240</span> <span style="color:#888; font-size:11px;">flete incluido</span><br><br>
                    <span style="color:#333;">&#191;Con cual le entramos?</span>
                    <div class="wa-msg-time">8:15 AM</div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============ PLATAFORMA COMPLETA ============ -->
<section class="platform" id="plataforma">
    <div class="container" style="text-align:center;">
        <div class="section-tag">Mas que cotizaciones</div>
        <div class="section-title">Plataforma Completa para tu Obra.</div>
        <div class="section-sub">Cotizar es solo el inicio. Controla compras, pagos, presupuesto y aprobaciones desde un solo lugar.</div>

        <div class="platform-grid" style="text-align:left;">
            <div class="platform-card">
                <div class="card-num">1</div>
                <h3>Portal de Seguimiento</h3>
                <p>Clientes y proveedores rastrean pedidos, costos, pagos y calificaciones en tiempo real. Todo desde tu navegador.</p>
            </div>
            <div class="platform-card">
                <div class="card-num">2</div>
                <h3>Pagos con Tarjeta</h3>
                <p>Paga directo desde la plataforma. Solo 2% de comision. Tu proveedor recibe el 98% completo. Sin intermediarios.</p>
            </div>
            <div class="platform-card">
                <div class="card-num">3</div>
                <h3>Control de Presupuesto</h3>
                <p>Sube tu presupuesto de obra. Cada pedido se descuenta automaticamente. Alertas al 50%, 80% y 100% de consumo.</p>
            </div>
            <div class="platform-card">
                <div class="card-num">4</div>
                <h3>Flujo de Aprobacion</h3>
                <p>Residente pide, compras valida, director autoriza. Cada empresa configura sus propias reglas y limites.</p>
            </div>
            <div class="platform-card">
                <div class="card-num">5</div>
                <h3>Inteligencia de Precios</h3>
                <p>Cada cotizacion alimenta nuestra base de datos. Detectamos tendencias, outliers y te avisamos cuando es buen momento para comprar.</p>
            </div>
            <div class="platform-card">
                <div class="card-num">6</div>
                <h3>Dashboard Analitico</h3>
                <p>Vista ejecutiva para duenos. Metricas de mercado, tendencias de precios, ranking de proveedores, todo en tiempo real.</p>
            </div>
        </div>
    </div>
</section>

<!-- ============ SOCIAL PROOF / METRICS ============ -->
<section class="proof">
    <div class="proof-grid">
        <div class="proof-card">
            <div class="proof-num" style="color:var(--orange);">30+</div>
            <div class="proof-label">Materiales disponibles</div>
        </div>
        <div class="proof-card">
            <div class="proof-num" style="color:var(--blue);">10+</div>
            <div class="proof-label">Proveedores conectados</div>
        </div>
        <div class="proof-card">
            <div class="proof-num" style="color:var(--green);">346</div>
            <div class="proof-label">Nombres reconocidos por la IA</div>
        </div>
        <div class="proof-card">
            <div class="proof-num" style="color:var(--navy);">< 5 min</div>
            <div class="proof-label">Cotizacion completa</div>
        </div>
    </div>
</section>

<!-- ============ MATERIALES ============ -->
<section class="materials" id="materiales">
    <div class="container" style="text-align:center;">
        <div class="section-tag">Catalogo</div>
        <div class="section-title">Todo lo que necesita tu obra.</div>
        <div class="section-sub">30 materiales principales. 7 categorias. Si lo usas en obra, lo cotizamos.</div>

        <div class="mat-grid">
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--orange);margin:0 auto 10px;"></div>
                <div class="mat-name">Concreto</div>
                <div class="mat-detail">f'c 150 a 300, bombeable</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--blue);margin:0 auto 10px;"></div>
                <div class="mat-name">Acero</div>
                <div class="mat-detail">Varilla, malla, armex, alambre</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--green);margin:0 auto 10px;"></div>
                <div class="mat-name">Agregados</div>
                <div class="mat-detail">Grava, arena, tepetate</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--navy);margin:0 auto 10px;"></div>
                <div class="mat-name">Cemento</div>
                <div class="mat-detail">Gris, blanco, cal, mortero</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--navy-mid);margin:0 auto 10px;"></div>
                <div class="mat-name">Block</div>
                <div class="mat-detail">Del 15, del 20, tabique</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--blue);margin:0 auto 10px;"></div>
                <div class="mat-name">Tuberia</div>
                <div class="mat-detail">PVC sanitario, hidraulico</div>
            </div>
            <div class="mat-card">
                <div class="mat-icon" style="width:12px;height:12px;border-radius:50%;background:var(--orange);margin:0 auto 10px;"></div>
                <div class="mat-name">Acabados</div>
                <div class="mat-detail">Impermeabilizante, cable</div>
            </div>
        </div>
    </div>
</section>

<!-- ============ PRECIOS REALES ============ -->
<section class="prices" id="precios">
    <div class="container" style="text-align:center;">
        <div class="section-tag" style="background:rgba(230,126,34,0.2); color:var(--orange);">Precios reales</div>
        <div class="section-title" style="color:#fff;">Compara antes de comprar.</div>
        <div class="section-sub" style="color:rgba(255,255,255,0.45);">Precios actualizados del mercado 2026. Flete incluido en la comparativa.</div>

        <div class="prices-grid">
            <div class="price-card">
                <div class="price-tag" style="color:var(--orange);">Concreto f'c 250</div>
                <div class="price-num">$2,280<span>/m3</span></div>
                <div class="price-detail">Desde $34,200 por olla de 15m3</div>
            </div>
            <div class="price-card">
                <div class="price-tag" style="color:var(--blue);">Varilla 3/8" G42</div>
                <div class="price-num">$82<span>/pza</span></div>
                <div class="price-detail">Desde $8,200 por 100 piezas</div>
            </div>
            <div class="price-card">
                <div class="price-tag" style="color:var(--green);">Block del 15</div>
                <div class="price-num">$11<span>/pza</span></div>
                <div class="price-detail">Desde $11,000 por millar</div>
            </div>
        </div>
    </div>
</section>

<!-- ============ CTA FINAL ============ -->
<section class="cta">
    <div class="cta-inner">
        <h2>Cotiza, compra, paga y controla &mdash;todo desde un solo lugar.</h2>
        <p>Plataforma completa para compras de obra. WhatsApp + Portal + Pagos + Presupuesto. Prueba gratis ahora.</p>
        <div class="cta-buttons">
            <a href="#" onclick="openAuth('register'); return false;" class="btn" style="background:#fff; color:var(--orange); font-weight:700;">Crear cuenta gratis &rarr;</a>
            <a href="#" onclick="openAuth('login'); return false;" class="btn btn-ghost-white">Ya tengo cuenta</a>
        </div>
    </div>
</section>

<!-- ============ FOOTER ============ -->
<footer>
    <div class="brand">ObraYa</div>
    <p>Cotizacion inteligente de materiales de construccion.</p>
    <p style="margin-top:4px;">Potenciado por IA &middot; LATAM &middot; 2026</p>
    <div class="footer-links">
        <a href="/sim/">Demo</a>
        <a href="/portal/">Portal</a>
        <a href="#plataforma">Presupuesto</a>
        <a href="/admin/">Admin</a>
        <a href="/docs">API</a>
        <a href="/health">Status</a>
    </div>
</footer>

<!-- Google Identity Services -->
<script src="https://accounts.google.com/gsi/client" async defer></script>
<!-- Microsoft MSAL -->

<!-- ============ SCROLL ANIMATION + AUTH ============ -->
<script>
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-up, .slide-right').forEach(el => observer.observe(el));

    // Hamburger menu toggle
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('nav-links');
    hamburger.addEventListener('click', function() {
        this.classList.toggle('active');
        navLinks.classList.toggle('open');
    });

    // Close menu when a nav link is clicked
    navLinks.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navLinks.classList.remove('open');
            // If it's an auth link, open modal (with delay for mobile menu animation)
            const authAction = this.getAttribute('data-auth');
            if (authAction) {
                const isMobile = navLinks.classList.contains('open') || window.innerWidth <= 900;
                setTimeout(() => openAuth(authAction), isMobile ? 200 : 0);
            }
        });
    });

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // ========== AUTH SYSTEM ==========

    function openAuth(tab) {
        document.getElementById('auth-overlay').classList.add('open');
        switchAuthTab(tab || 'login');
        document.getElementById('auth-error').style.display = 'none';
        document.getElementById('auth-success').style.display = 'none';
        // Re-render Google button (needs visible container)
        setTimeout(initGoogleSignIn, 100);
    }

    function closeAuth() {
        document.getElementById('auth-overlay').classList.remove('open');
    }

    function switchAuthTab(tab) {
        const tabs = document.querySelectorAll('.auth-tab');
        tabs[0].classList.toggle('active', tab === 'login');
        tabs[1].classList.toggle('active', tab === 'register');
        document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
        document.getElementById('auth-title').textContent = tab === 'login' ? 'Iniciar sesion' : 'Crear cuenta';
        document.getElementById('auth-subtitle').textContent = tab === 'login'
            ? 'Accede a tu cuenta de ObraYa'
            : 'Registrate como comprador o proveedor';
        document.getElementById('auth-error').style.display = 'none';
        document.getElementById('auth-success').style.display = 'none';
    }

    function selectRole(role) {
        document.getElementById('reg-role').value = role;
        document.getElementById('role-comprador').classList.toggle('active', role === 'comprador');
        document.getElementById('role-proveedor').classList.toggle('active', role === 'proveedor');
    }

    function showAuthError(msg) {
        const el = document.getElementById('auth-error');
        el.textContent = msg;
        el.style.display = 'block';
        document.getElementById('auth-success').style.display = 'none';
    }

    function showAuthSuccess(msg) {
        const el = document.getElementById('auth-success');
        el.textContent = msg;
        el.style.display = 'block';
        document.getElementById('auth-error').style.display = 'none';
    }

    async function handleLogin(e) {
        e.preventDefault();
        const btn = document.getElementById('login-btn');
        btn.disabled = true;
        btn.textContent = 'Entrando...';

        try {
            const resp = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: document.getElementById('login-email').value,
                    password: document.getElementById('login-password').value,
                }),
            });
            const data = await resp.json();
            if (data.ok) {
                localStorage.setItem('obraya_token', data.token);
                localStorage.setItem('obraya_user', JSON.stringify(data.user));
                showAuthSuccess('Bienvenido, ' + data.user.nombre);
                setTimeout(() => {
                    closeAuth();
                    updateNavForUser(data.user);
                    window.location.href = '/portal/';
                }, 800);
            } else {
                showAuthError(data.error);
            }
        } catch (err) {
            showAuthError('Error de conexion. Intenta de nuevo.');
        }
        btn.disabled = false;
        btn.textContent = 'Iniciar sesion';
    }

    async function handleRegister(e) {
        e.preventDefault();
        const btn = document.getElementById('register-btn');
        btn.disabled = true;
        btn.textContent = 'Creando cuenta...';

        const role = document.getElementById('reg-role').value;
        try {
            const resp = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: document.getElementById('reg-email').value,
                    password: document.getElementById('reg-password').value,
                    nombre: document.getElementById('reg-nombre').value,
                    telefono: document.getElementById('reg-telefono').value,
                    telefono_codigo_pais: document.getElementById('reg-country-code').value,
                    empresa: document.getElementById('reg-empresa').value,
                    tipo: role,
                    es_proveedor: role === 'proveedor',
                }),
            });
            const data = await resp.json();
            if (data.ok) {
                localStorage.setItem('obraya_token', data.token);
                localStorage.setItem('obraya_user', JSON.stringify(data.user));
                showAuthSuccess('Cuenta creada. Bienvenido!');
                setTimeout(() => {
                    closeAuth();
                    updateNavForUser(data.user);
                    window.location.href = '/portal/';
                }, 800);
            } else {
                showAuthError(data.error);
            }
        } catch (err) {
            showAuthError('Error de conexion. Intenta de nuevo.');
        }
        btn.disabled = false;
        btn.textContent = 'Crear cuenta';
    }

    // ========== OAUTH: Google ==========
    function initGoogleSignIn() {
        const gClientId = '__GOOGLE_CLIENT_ID__';
        if (!gClientId || typeof google === 'undefined' || !google.accounts) return;
        google.accounts.id.initialize({
            client_id: gClientId,
            callback: handleGoogleResponse,
        });
        google.accounts.id.renderButton(
            document.getElementById('google-signin-btn'),
            { theme: 'outline', size: 'large', width: 340, text: 'continue_with', locale: 'es' }
        );
    }
    // Render on load and also when modal opens (in case it wasn't visible)
    if (typeof google !== 'undefined' && google.accounts) {
        initGoogleSignIn();
    } else {
        window.addEventListener('load', initGoogleSignIn);
    }

    async function handleGoogleResponse(response) {
        try {
            const resp = await fetch('/auth/oauth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: response.credential, provider: 'google' }),
            });
            const data = await resp.json();
            if (data.ok) {
                localStorage.setItem('obraya_token', data.token);
                localStorage.setItem('obraya_user', JSON.stringify(data.user));
                closeAuth();
                updateNavForUser(data.user);
                window.location.href = '/portal/';
            } else {
                showAuthError(data.error);
            }
        } catch (err) {
            showAuthError('Error con Google. Intenta con email.');
        }
    }


    // ========== NAV UPDATE ==========
    function updateNavForUser(user) {
        document.getElementById('nav-login-btn').style.display = 'none';
        document.getElementById('nav-register-btn').style.display = 'none';
        const menu = document.getElementById('nav-user-menu');
        menu.style.display = 'flex';
        const avatar = document.getElementById('nav-user-avatar');
        if (user.avatar_url) {
            avatar.innerHTML = '<img src="' + user.avatar_url + '" alt="">';
        } else {
            avatar.textContent = (user.nombre || 'U')[0].toUpperCase();
        }
    }

    // ========== CHECK EXISTING SESSION ==========
    (function checkSession() {
        const token = localStorage.getItem('obraya_token');
        const user = localStorage.getItem('obraya_user');
        if (token && user) {
            try {
                const u = JSON.parse(user);
                updateNavForUser(u);
            } catch(e) {}
        }
    })();
</script>

</body>
</html>
"""
    # Inject OAuth client IDs
    html = html.replace("__GOOGLE_CLIENT_ID__", settings.GOOGLE_CLIENT_ID)
    return html
