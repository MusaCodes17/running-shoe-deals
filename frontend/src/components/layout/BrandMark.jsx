import { cn } from '@/lib/utils'

/**
 * Anton's app mark: a forward-leaning "A" monogram — an italic A whose apex
 * sits right of its base so the whole letter leans into a stride, with the
 * crossbar drawn as a motion line that overshoots the right leg into a trail.
 * Name + movement in one glyph.
 *
 * Strokes use `currentColor`, so the caller controls colour (dark strokes on
 * the green tile inside the app; green strokes on their own for the favicon).
 */
export default function BrandMark({ className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={cn('shrink-0', className)}
      aria-hidden="true"
    >
      <g
        stroke="currentColor"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* left leg (long, shallow) → apex shifted right = the forward lean */}
        <path d="M12.6 4.4 L4 19.6" />
        {/* right leg (short, steep) */}
        <path d="M12.6 4.4 L15.6 19.6" />
        {/* crossbar as a motion line, overshooting the right leg into a trail */}
        <path d="M7 15 L20 12.4" />
      </g>
    </svg>
  )
}
