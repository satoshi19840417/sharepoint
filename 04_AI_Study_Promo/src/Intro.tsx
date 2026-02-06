import { AbsoluteFill, useVideoConfig, spring, useCurrentFrame } from 'remotion';
import { Typewriter } from './components/Typewriter';

export const Intro = () => {
    // 問いかけ。「AI、ただのチャットだと思っていませんか？」
    // シンプルなチャット画面。「Hello」の文字。背景は少し退屈なグレー
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const scale = spring({
        frame,
        fps,
        config: {
            damping: 12,
        },
    });

    return (
        <AbsoluteFill className="items-center justify-center font-sans">
            <div style={{ transform: `scale(${scale})` }} className="bg-white p-10 rounded-2xl shadow-xl w-3/4 max-w-4xl border border-gray-200">
                <div className="flex items-center mb-6">
                    <div className="w-4 h-4 rounded-full bg-red-400 mr-2"></div>
                    <div className="w-4 h-4 rounded-full bg-yellow-400 mr-2"></div>
                    <div className="w-4 h-4 rounded-full bg-green-400"></div>
                </div>
                <div className="space-y-4">
                    <div className="flex justify-end">
                        <div className="bg-blue-500 text-white p-4 rounded-t-xl rounded-bl-xl max-w-lg">
                            <Typewriter text="AIって、ただのチャットボットだよね？" speed={3} cursor={false} />
                        </div>
                    </div>
                    <div className="flex justify-start">
                        {frame > 60 && (
                            <div className="bg-gray-200 text-gray-800 p-4 rounded-t-xl rounded-br-xl max-w-lg animate-bounce-in">
                                <Typewriter text="今日はそれが変わります！" speed={2} delay={60} />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </AbsoluteFill>
    );
};
