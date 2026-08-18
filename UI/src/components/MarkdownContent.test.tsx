import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MarkdownContent } from './MarkdownContent';

describe('MarkdownContent', () => {
  it('renders a single newline as a line break', () => {
    const { container } = render(<MarkdownContent source={'First line\nSecond line'} />);

    expect(container.querySelector('br')).toBeInTheDocument();
    expect(screen.getByText(/First line/)).toHaveTextContent('First line');
    expect(screen.getByText(/Second line/)).toHaveTextContent('Second line');
  });

  it('renders Markdown while dropping raw HTML and unsafe URLs', () => {
    const { container } = render(
      <MarkdownContent source={'**Safe** <script>alert(1)</script> [bad](javascript:alert(1))'} />,
    );

    expect(screen.getByText('Safe').tagName).toBe('STRONG');
    expect(container.querySelector('script')).not.toBeInTheDocument();
    expect(screen.getByText('bad').closest('a')).toHaveAttribute('href', '');
  });
});
