import { AbsoluteFill, Sequence, staticFile, useCurrentFrame, interpolate } from 'remotion';
import { Audio } from '@remotion/media';
import { Intro } from './Intro';
import { Hook } from './Hook';
import { Body } from './Body';
import { Outro } from './Outro';
import { BackgroundParticles } from './components/BackgroundParticles';
import { SceneTransition } from './components/SceneTransition';

export const MainComposition = ({ bgmSource = "bgm.mp3" }: { bgmSource?: string }) => {
    // Total duration: 30s (900 frames at 30fps)
    // Overlap duration: 30 frames (1s)

    // Sequence timings:
    // Intro: 0 - 180 (Exit overlap: 150-180)
    // Hook: 150 - 480 (Enter: 150-180, Exit: 450-480). Duration 330.
    // Body: 450 - 780 (Enter: 450-480, Exit: 750-780). Duration 330.
    // Outro: 750 - 900 (Enter: 750-780). Duration 150.

    return (
        <AbsoluteFill className="bg-black">
            <BackgroundParticles count={100} />
            <Audio src={staticFile(bgmSource)} volume={0.5} />

            <Sequence from={0} durationInFrames={180}>
                <IntroTransition />
            </Sequence>
            <Sequence from={150} durationInFrames={330}>
                <HookTransition />
            </Sequence>
            <Sequence from={450} durationInFrames={330}>
                <BodyTransition />
            </Sequence>
            <Sequence from={750} durationInFrames={150}>
                <OutroTransition />
            </Sequence>
        </AbsoluteFill>
    );
};

const IntroTransition = () => {
    const frame = useCurrentFrame();
    // Exit starts at 150 (relative frame 150 of 180)
    const exit = interpolate(frame, [150, 180], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
        <SceneTransition enterProgress={1} exitProgress={exit}>
            <Intro />
        </SceneTransition>
    );
};

const HookTransition = () => {
    const frame = useCurrentFrame();
    // Enter 0-30, Exit 300-330
    const enter = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const exit = interpolate(frame, [300, 330], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
        <SceneTransition enterProgress={enter} exitProgress={exit}>
            <Hook />
        </SceneTransition>
    );
};

const BodyTransition = () => {
    const frame = useCurrentFrame();
    // Enter 0-30, Exit 300-330
    const enter = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const exit = interpolate(frame, [300, 330], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
        <SceneTransition enterProgress={enter} exitProgress={exit}>
            <Body />
        </SceneTransition>
    );
};

const OutroTransition = () => {
    const frame = useCurrentFrame();
    // Enter 0-30
    const enter = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
        <SceneTransition enterProgress={enter} exitProgress={0}>
            <Outro />
        </SceneTransition>
    );
};
