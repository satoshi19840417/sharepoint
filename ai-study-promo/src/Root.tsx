import { Composition, Folder } from 'remotion';
import { MainComposition } from './MainComposition';
import { Intro } from './Intro';
import { Hook } from './Hook';
import { Body } from './Body';
import { Outro } from './Outro';
import './style.css';

export const RemotionRoot = () => {
    return (
        <>
            <Folder name="Scenes">
                {/* Individual scenes will be added here for individual preview */}
            </Folder>
            <Composition
                id="MainComposition-A"
                component={MainComposition}
                durationInFrames={30 * 30}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    bgmSource: "Aイノベーション.mp3",
                }}
            />
            <Composition
                id="MainComposition-B"
                component={MainComposition}
                durationInFrames={30 * 30}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    bgmSource: "B青空.mp3",
                }}
            />
            <Composition
                id="MainComposition-C"
                component={MainComposition}
                durationInFrames={30 * 30}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    bgmSource: "CAncient_memories.mp3",
                }}
            />
            <Composition
                id="MainComposition-Final"
                component={MainComposition}
                durationInFrames={30 * 30}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    bgmSource: "Tech-Cube.mp3",
                }}
            />
        </>
    );
};
