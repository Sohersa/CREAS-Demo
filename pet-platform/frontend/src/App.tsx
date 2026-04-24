import Twin from "./pages/Twin";
import "./ui.css";

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">AX</div>
      </aside>
      <header className="topbar">
        <b>AXIS</b> &nbsp;/&nbsp; Planta PET Monterrey &nbsp;/&nbsp; <b>Línea 2</b>
      </header>
      <main className="main">
        <Twin />
      </main>
    </div>
  );
}
