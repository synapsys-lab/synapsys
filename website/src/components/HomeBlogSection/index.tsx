import type { ReactElement } from 'react';
import { useState, useEffect } from 'react';
import Link from '@docusaurus/Link';
import Translate, { translate } from '@docusaurus/Translate';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface BlogPost {
  title: string;
  description: string;
  href: string;
  date: string;
  readingTime?: number;
  image?: string;
  tags: string[];
  contentType: 'artigo' | 'post';
}

const BLOG_POSTS: BlogPost[] = [
  {
    title: 'PID with Anti-Windup: Theory, Tuning and Experimental Validation',
    description:
      'A research-oriented deep-dive into discrete PID with back-calculation anti-windup — from the integral windup problem to experimental step-response validation, with Synapsys code throughout.',
    href: '/blog/pid-anti-windup-research',
    date: '2026-04-23',
    readingTime: 12,
    image: '/img/quickstart/qs_04_pid.png',
    tags: ['pid', 'control-theory', 'simulation'],
    contentType: 'artigo',
  },
  {
    title: 'MIMO Control of a Quadcopter with Neural-LQR',
    description:
      'How to model a 12-state linearised quadrotor, design a MIMO LQR, augment it with a residual MLP, and simulate the closed-loop in 3D — a research-grade case study using Synapsys.',
    href: '/blog/quadcopter-mimo-neural-lqr',
    date: '2026-04-21',
    readingTime: 15,
    tags: ['mimo', 'lqr', 'neural-lqr', 'simulation'],
    contentType: 'artigo',
  },
  {
    title: 'From Model to Hardware: MIL → SIL → HIL in Three Steps',
    description:
      'A practical guide to the MIL/SIL/HIL development workflow with Synapsys — swap from simulation to real hardware by changing one line, keeping your control algorithm untouched.',
    href: '/blog/mil-sil-hil-control-deployment',
    date: '2026-04-22',
    readingTime: 8,
    image: '/img/examples/03_sil_ai_controller.png',
    tags: ['sil', 'hil', 'simulation'],
    contentType: 'post',
  },
  {
    title: 'Stabilising an Inverted Pendulum with LQR',
    description:
      'A complete walkthrough: derive the linearised state-space model of an inverted pendulum, design an LQR controller, simulate the closed-loop response, and discretise for embedded deployment — all in Python with Synapsys.',
    href: '/blog/inverted-pendulum-lqr',
    date: '2026-04-20',
    readingTime: 10,
    tags: ['lqr', 'control-theory', 'simulation'],
    contentType: 'artigo',
  },
  {
    title: 'Welcome to the Synapsys Blog',
    description:
      'Introducing the Synapsys Blog — a space for tutorials, research insights, and practical guides for control systems engineers and researchers.',
    href: '/blog/welcome-to-synapsys-blog',
    date: '2026-04-19',
    readingTime: 3,
    tags: ['release', 'python'],
    contentType: 'post',
  },
];

// Track layout: [clone-of-last, ...BLOG_POSTS, clone-of-first]
// trackIdx 1..N = real slides; 0 = clone-of-last; N+1 = clone-of-first
const TOTAL = BLOG_POSTS.length;
const TRACK_SLIDES = [BLOG_POSTS[TOTAL - 1], ...BLOG_POSTS, BLOG_POSTS[0]];

function BlogSlide({ post }: { post: BlogPost }): ReactElement {
  const imageUrl = useBaseUrl(post.image ?? '');
  const { i18n } = useDocusaurusContext();
  const displayDate = new Date(post.date).toLocaleDateString(i18n.currentLocale, {
    year: 'numeric', month: 'long', day: 'numeric',
  });
  const badgeClass = post.contentType === 'artigo'
    ? 'hbc__badge hbc__badge--artigo'
    : 'hbc__badge hbc__badge--post';

  return (
    <div className={post.image ? 'hbc__slide' : 'hbc__slide hbc__slide--no-image'}>
      {post.image && (
        <Link to={post.href} className="hbc__media">
          <img src={imageUrl} alt={post.title} className="hbc__image" />
        </Link>
      )}
      <div className="hbc__body">
        <span className={badgeClass}>
          {post.contentType === 'artigo'
            ? translate({ id: 'home.blog.badge.artigo', message: 'Article' })
            : translate({ id: 'home.blog.badge.post', message: 'Post' })}
        </span>
        <h3 className="hbc__title">
          <Link to={post.href}>{post.title}</Link>
        </h3>
        <p className="hbc__meta">
          <time dateTime={post.date}>{displayDate}</time>
          {post.readingTime !== undefined && (
            <span> · {post.readingTime} {translate({ id: 'home.blog.read_time', message: 'min read' })}</span>
          )}
        </p>
        <p className="hbc__desc">{post.description}</p>
        <div className="hbc__tags">
          {post.tags.slice(0, 4).map((tag) => (
            <Link key={tag} to={`/blog/tags/${tag}`} className="hbc__tag">{tag}</Link>
          ))}
        </div>
        <Link to={post.href} className="hbc__cta">
          <Translate id="home.blog.read_more">Read full article →</Translate>
        </Link>
      </div>
    </div>
  );
}

function BlogCarousel(): ReactElement {
  const [trackIdx, setTrackIdx] = useState(1);
  const [animated, setAnimated] = useState(true);
  const [paused, setPaused] = useState(false);

  const realIdx = trackIdx <= 0 ? TOTAL - 1 : trackIdx > TOTAL ? 0 : trackIdx - 1;

  const goTo = (ti: number) => { setAnimated(true); setTrackIdx(ti); };
  const prev = () => { setPaused(true); goTo(trackIdx - 1); };
  const next = () => { setPaused(true); goTo(trackIdx + 1); };

  const handleTransitionEnd = (e: React.TransitionEvent<HTMLDivElement>) => {
    if (e.target !== e.currentTarget) return;
    if (trackIdx === 0) {
      setAnimated(false);
      setTrackIdx(TOTAL);
    } else if (trackIdx === TOTAL + 1) {
      setAnimated(false);
      setTrackIdx(1);
    }
  };

  useEffect(() => {
    if (paused) return;
    const timer = setInterval(() => { setAnimated(true); setTrackIdx((i) => i + 1); }, 5000);
    return () => clearInterval(timer);
  }, [paused]);

  return (
    <div className="hbc" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="hbc__viewport">
        <div
          className="hbc__track"
          style={{
            transform: `translateX(-${trackIdx * 100}%)`,
            transition: animated ? 'transform 0.45s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
          }}
          onTransitionEnd={handleTransitionEnd}
        >
          {TRACK_SLIDES.map((post, i) => <BlogSlide key={i} post={post} />)}
        </div>
      </div>

      <div className="hbc__controls">
        <button onClick={prev} className="hbc__btn" aria-label={translate({ id: 'home.blog.prev', message: 'Previous' })}>
          <ChevronLeft size={18} strokeWidth={2} />
        </button>
        <div className="hbc__dots">
          {BLOG_POSTS.map((_, i) => (
            <button
              key={i}
              onClick={() => { setPaused(true); goTo(i + 1); }}
              className={i === realIdx ? 'hbc__dot hbc__dot--active' : 'hbc__dot'}
              aria-label={`Post ${i + 1}`}
            />
          ))}
        </div>
        <button onClick={next} className="hbc__btn" aria-label={translate({ id: 'home.blog.next', message: 'Next' })}>
          <ChevronRight size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}

export default function HomeBlogSection(): ReactElement {
  return (
    <section className="content-section content-section--alt">
      <div className="content-section__inner">
        <h2 className="content-section__title">
          <Translate id="home.blog.title">From the Blog</Translate>
        </h2>
        <p className="content-section__lead">
          <Translate id="home.blog.lead">
            In-depth research articles and practical posts on control systems, AI and Synapsys.
          </Translate>
        </p>
        <BlogCarousel />
        <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
          <Link to="/blog" className="button button--outline button--sm button--primary">
            <Translate id="home.blog.all">See all posts →</Translate>
          </Link>
        </div>
      </div>
    </section>
  );
}
