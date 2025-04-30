'use client';

interface FileSelectProps {
    onSelect: (videoId: string) => void;
}

export default function FileSelect({ onSelect }: FileSelectProps) {
    const handleClick = () => {
        const select = document.getElementById('option-select') as HTMLSelectElement;
        const selectedValue = select.value;
        if (selectedValue) {
            onSelect(selectedValue);
        }
    };

    return (
        <div className="mb-4 px-24">
            <div className="flex items-center gap-4 h-10">
                <label className="font-semibold">유튜브 선택: </label>
                <select
                    id="option-select"
                    className="h-8 px-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-[60%]"
                >
                    <option value="">선택하세요.</option>
                    <option value="UibfDUPJAEU">Commencement of Author J.K Rowling</option>
                    <option value="Gzu9S5FL-Ug">Commencement of Justice John Roberts</option>
                </select>
                <button
                    onClick={handleClick}
                    className="h-8 w-28 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                    실행
                </button>
            </div>
            <div className="relative mt-2 px-24 mx-2"></div>
        </div>
    );
}
