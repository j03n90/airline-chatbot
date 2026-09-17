import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

function safeHref(href: string | undefined): string | undefined {
  if (!href) return undefined;
  if (/^(https?:|mailto:)/i.test(href)) return href;
  return undefined;
}

const components: Components = {
  a({ href, children }) {
    const safe = safeHref(href);
    if (!safe) return <span>{children}</span>;
    return (
      <a href={safe} target="_blank" rel="noreferrer noopener">
        {children}
      </a>
    );
  },
  img({ alt }) {
    return alt ? <span>{alt}</span> : null;
  },
};

export default function MarkdownMessage({ text }: { text: string }) {
  return (
    <div className="md">
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
