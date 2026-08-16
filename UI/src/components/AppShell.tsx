import { NavLink, Outlet } from 'react-router-dom';
import styles from './AppShell.module.css';

const links = [
  { to: '/', label: 'Today', shortLabel: '01', end: true },
  { to: '/focus', label: 'Focus', shortLabel: '02', end: false },
];

export function AppShell() {
  return (
    <div className={styles.shell}>
      <aside className={styles.rail} aria-label="Primary navigation">
        <NavLink to="/" className={styles.mark} aria-label="StudyHub home">
          SH
        </NavLink>
        <nav className={styles.nav}>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
            >
              <span className={styles.index} aria-hidden="true">{link.shortLabel}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <p className={styles.railNote}>Quiet work,<br />kept visible.</p>
      </aside>

      <main className={styles.main}>
        <Outlet />
      </main>

      <nav className={styles.mobileNav} aria-label="Primary navigation">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => `${styles.mobileLink} ${isActive ? styles.mobileActive : ''}`}
          >
            <span aria-hidden="true">{link.shortLabel}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
