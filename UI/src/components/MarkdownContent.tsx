import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import styles from './MarkdownContent.module.css';

interface MarkdownContentProps {
  source: string;
  className?: string;
}

export function MarkdownContent({ source, className }: MarkdownContentProps) {
  return (
    <div className={`${styles.markdown} ${className ?? ''}`}>
      <ReactMarkdown remarkPlugins={[remarkBreaks]} skipHtml>
        {source}
      </ReactMarkdown>
    </div>
  );
}
