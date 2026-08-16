import styles from './StatusBlock.module.css';

interface StatusBlockProps {
  title: string;
  detail?: string;
  tone?: 'quiet' | 'error';
  action?: React.ReactNode;
}

export function StatusBlock({ title, detail, tone = 'quiet', action }: StatusBlockProps) {
  return (
    <div className={`${styles.block} ${tone === 'error' ? styles.error : ''}`} role={tone === 'error' ? 'alert' : 'status'}>
      <p className={styles.title}>{title}</p>
      {detail && <p className={styles.detail}>{detail}</p>}
      {action}
    </div>
  );
}
