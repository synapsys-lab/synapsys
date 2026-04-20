import React, {useState} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import BlogLayout from '@theme/BlogLayout';
import {
  HtmlClassNameProvider,
  PageMetadata,
  ThemeClassNames,
} from '@docusaurus/theme-common';
import BlogListPaginator from '@theme/BlogListPaginator';
import BlogPostItems from '@theme/BlogPostItems';
import SearchMetadata from '@theme/SearchMetadata';
import BlogListPageStructuredData from '@theme/BlogListPage/StructuredData';
import type {Props} from '@theme/BlogListPage';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {BookOpen, PenLine, ChevronLeft, ChevronRight} from 'lucide-react';
import styles from './styles.module.css';

// ── Featured Carousel (full-width) ───────────────────────────────────────────

function CarouselSlide({item, onPrev, onNext, index, total}: {
  item: Props['items'][number];
  onPrev: () => void;
  onNext: () => void;
  index: number;
  total: number;
  onDot: (i: number) => void;
}): React.ReactElement {
  const {metadata, frontMatter} = item.content;
  const {permalink, title, description, date, readingTime, tags} = metadata;
  const rawImage = (frontMatter as {image?: string}).image ?? '';
  const imageUrl = useBaseUrl(rawImage);
  const displayDate = new Date(date).toLocaleDateString('pt-BR', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
  return (
    <div className={styles.featuredInner} key={permalink}>
      <div className={styles.featuredText}>
        <p className={styles.featuredLabel}>Artigo em Destaque</p>
        <h2 className={styles.featuredTitle}><Link href={permalink}>{title}</Link></h2>
        <p className={styles.featuredMeta}>
          <time dateTime={date}>{displayDate}</time>
          {readingTime !== undefined && <span> · {Math.ceil(readingTime)} min de leitura</span>}
        </p>
        {description && <p className={styles.featuredDescription}>{description}</p>}
        {tags.length > 0 && (
          <div className={styles.featuredTags}>
            {tags.filter((t) => t.label.toLowerCase() !== 'artigo').slice(0, 4).map((tag) => (
              <Link key={tag.permalink} href={tag.permalink} className={styles.tag}>{tag.label}</Link>
            ))}
          </div>
        )}
        <Link href={permalink} className={styles.featuredCta}>Ler artigo completo →</Link>
      </div>
      <div className={styles.featuredMedia}>
        {rawImage ? (
          <Link href={permalink}><img src={imageUrl} alt={title} className={styles.featuredImage} /></Link>
        ) : (
          <div className={styles.featuredPlaceholder} />
        )}
      </div>
    </div>
  );
}

function FeaturedCarousel({items}: {items: Props['items']}): React.ReactElement | null {
  const [index, setIndex] = useState(0);
  if (items.length === 0) return null;

  const prev = () => setIndex((i) => (i - 1 + items.length) % items.length);
  const next = () => setIndex((i) => (i + 1) % items.length);

  return (
    <div className={styles.featured}>
      <CarouselSlide
        item={items[index]}
        onPrev={prev}
        onNext={next}
        index={index}
        total={items.length}
        onDot={setIndex}
      />
      {items.length > 1 && (
        <div className={styles.featuredControls}>
          <button onClick={prev} className={styles.carouselBtn} aria-label="Anterior">
            <ChevronLeft size={18} strokeWidth={2} />
          </button>
          <div className={styles.carouselDots}>
            {items.map((_, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                className={clsx(styles.dot, i === index && styles.dotActive)}
                aria-label={`Slide ${i + 1}`}
              />
            ))}
          </div>
          <button onClick={next} className={styles.carouselBtn} aria-label="Próximo">
            <ChevronRight size={18} strokeWidth={2} />
          </button>
        </div>
      )}
    </div>
  );
}

// ── Blog Section ──────────────────────────────────────────────────────────────

interface SectionProps {
  title: string;
  subtitle: string;
  variant: 'artigo' | 'post';
  allHref: string;
  items: Props['items'];
}

function BlogSection({title, subtitle, variant, allHref, items}: SectionProps): React.ReactElement {
  return (
    <section className={clsx(styles.section, styles[`section--${variant}`])}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionHeadingRow}>
          <h2 className={clsx(styles.sectionTitle, styles[`sectionTitle--${variant}`])}>
            {title}
            <span className={styles.sectionCount}>{items.length}</span>
          </h2>
          <Link href={allHref} className={clsx(styles.seeAll, styles[`seeAll--${variant}`])}>
            Ver todos →
          </Link>
        </div>
        <p className={styles.sectionSubtitle}>{subtitle}</p>
        <hr className={clsx(styles.sectionDivider, styles[`sectionDivider--${variant}`])} />
      </div>
      {items.length === 0 ? (
        <p className={styles.emptyState}>Nenhum conteúdo ainda.</p>
      ) : (
        <BlogPostItems items={items} />
      )}
    </section>
  );
}

// ── Page metadata ─────────────────────────────────────────────────────────────

function BlogListPageMetadata({metadata}: Props): React.ReactElement {
  const {siteConfig} = useDocusaurusContext();
  const {blogDescription, blogTitle, permalink} = metadata;
  const isBlogOnlyMode = permalink === '/';
  const title = isBlogOnlyMode ? siteConfig.title : blogTitle;
  return (
    <>
      <PageMetadata title={title} description={blogDescription} />
      <SearchMetadata tag="blog_posts_list" />
    </>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function BlogListPage(props: Props): React.ReactElement {
  const {metadata, items, sidebar} = props;

  const artigosHref = useBaseUrl('/blog/tags/artigo');
  const postsHref   = useBaseUrl('/blog/tags/post');

  const artigos = items.filter(
    ({content}) =>
      (content.frontMatter as {content_type?: string}).content_type === 'artigo',
  );
  const posts = items.filter(
    ({content}) =>
      (content.frontMatter as {content_type?: string}).content_type !== 'artigo',
  );

  const isFirstPage = metadata.page === 1;

  return (
    <HtmlClassNameProvider
      className={clsx(
        ThemeClassNames.wrapper.blogPages,
        ThemeClassNames.page.blogListPage,
      )}>
      <BlogListPageMetadata {...props} />
      <BlogListPageStructuredData {...props} />

      {isFirstPage ? (
        <Layout>
          <div className={styles.hubWrap}>

            {/* ① Hero */}
            <header className={styles.hero}>
              <h1 className={styles.heroTitle}>Blog</h1>
              <p className={styles.heroSubtitle}>
                Artigos de pesquisa aprofundados e posts práticos sobre controle de
                sistemas, IA e Synapsys.
              </p>
              <div className={styles.heroNav}>
                <Link href={artigosHref} className={clsx(styles.heroNavBtn, styles['heroNavBtn--artigo'])}>
                  <BookOpen size={15} strokeWidth={2} /> Todos os Artigos
                </Link>
                <Link href={postsHref} className={clsx(styles.heroNavBtn, styles['heroNavBtn--post'])}>
                  <PenLine size={15} strokeWidth={2} /> Todos os Posts
                </Link>
              </div>
            </header>

            {/* ② Destaque — carrossel full-width */}
            <FeaturedCarousel items={artigos} />

            {/* ③ Duas colunas — previews nativos */}
            <div className={styles.columns}>
              <BlogSection
                title="Artigos"
                subtitle="Pesquisa aprofundada, modelagem matemática e estudos de caso."
                variant="artigo"
                allHref={artigosHref}
                items={artigos}
              />
              <BlogSection
                title="Posts"
                subtitle="Tutoriais rápidos, novidades e dicas práticas."
                variant="post"
                allHref={postsHref}
                items={posts}
              />
            </div>

          </div>
        </Layout>
      ) : (
        <BlogLayout sidebar={sidebar}>
          <BlogPostItems items={items} />
          <BlogListPaginator metadata={metadata} />
        </BlogLayout>
      )}
    </HtmlClassNameProvider>
  );
}
