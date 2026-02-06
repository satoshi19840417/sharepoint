import { useCurrentFrame } from 'remotion';

export const Typewriter = ({
    text,
    speed = 5,
    cursor = true,
    delay = 0,
}: {
    text: string;
    speed?: number;
    cursor?: boolean;
    delay?: number;
}) => {
    const frame = useCurrentFrame();
    const charsShown = Math.floor(Math.max(0, frame - delay) / speed);
    const currentText = text.slice(0, charsShown);

    // Blinking cursor
    const showCursor = cursor && Math.floor(frame / 15) % 2 === 0;

    return (
        <span>
            {currentText}
            {showCursor && <span className="opacity-100">|</span>}
            {!showCursor && cursor && <span className="opacity-0">|</span>}
        </span>
    );
};
