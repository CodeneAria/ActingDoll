/**
 * Background Color Controller
 * HTMLのコントロールパネルから背景色を制御するモジュール
 */

import { CubismLogInfo, CubismLogError } from '@framework/utils/cubismdebug';

/**
 * 背景色コントローラークラス
 */
export class BackgroundColorController {
    private colorInputElement: HTMLInputElement | null = null;
    private colorPickerElement: HTMLInputElement | null = null;
    private colorValueElement: HTMLElement | null = null;
    private canvasElement: HTMLCanvasElement | null = null;

    /**
     * コンストラクタ
     * @param initialColor - 初期背景色（#XXXXXX形式）
     * @param initialAlpha - 初期背景色のアルファ値（0.0〜1.0）
     */
    constructor(initialColor: string = '#FFFFFF', initialAlpha: number = 1.0) {
        this.ColorA = Math.max(0.0, Math.min(1.0, initialAlpha)); // アルファ値を0.0〜1.0の範囲に制限
        this.initialize();
        this.applyBackgroundColor(initialColor);
        this.updateUI(initialColor);
    }

    /**
     * 初期化
     */
    private initialize(): void {
        // HTMLエレメントを取得
        this.colorInputElement = document.getElementById('backgroundColorInput') as HTMLInputElement;
        this.colorPickerElement = document.getElementById('backgroundColorPicker') as HTMLInputElement;
        this.colorValueElement = document.getElementById('backgroundColorValue');
        this.canvasElement = document.querySelector('canvas') as HTMLCanvasElement;

        if (!this.colorInputElement || !this.colorPickerElement) {
            CubismLogError('Background color controller elements not found');
            return;
        }

        // イベントハンドラを登録
        this.setupEventHandlers();
    }

    /**
     * リソースの解放
     * イベントリスナーの削除
     */
    public release(): void {
        if (this.colorInputElement) {
            this.colorInputElement.removeEventListener('change', this.onColorChange);
            this.colorInputElement.removeEventListener('input', this.onColorInput);
        }

        if (this.colorPickerElement) {
            this.colorPickerElement.removeEventListener('change', this.onColorPickerInputChange);
            this.colorPickerElement.removeEventListener('input', this.onColorPickerInputChange);
        }
    }

    /**
     * イベントハンドラを設定
     */
    private setupEventHandlers(): void {
        if (!this.colorInputElement || !this.colorPickerElement) return;

        // テキスト入力フィールドの変更イベント
        this.colorInputElement.addEventListener('change', this.onColorChange);
        // テキスト入力フィールドのリアルタイム入力
        this.colorInputElement.addEventListener('input', this.onColorInput);
        // カラーピッカーの変更イベント
        this.colorPickerElement.addEventListener('change', this.onColorPickerInputChange);
        // カラーピッカーのドラッグ中のリアルタイム入力
        this.colorPickerElement.addEventListener('input', this.onColorPickerInputChange);
    }

    /**
     * テキスト入力フィールドの変更イベントハンドラ
     * @param e - イベントオブジェクト
     */
    private onColorChange = (e: Event): void => {
        const input = e.target as HTMLInputElement;
        const color = this.validateAndFormatColor(input.value);
        if (color) {
            this.applyBackgroundColor(color);
            this.updateUI(color);
        } else {
            // 無効な入力の場合、前の値に戻す
            input.value = this.colorInputElement?.value || '#FFFFFF';
        }
        CubismLogInfo(`Background color changed to ${color}`);
    }
    /**
     * テキスト入力フィールドのリアルタイム入力イベントハンドラ
     * @param e - イベントオブジェクト
     */
    private onColorInput = (e: Event): void => {
        const input = e.target as HTMLInputElement;
        // ユーザーが入力中に検証（ただし完全な値でなくてもOK）
        if (input.value.length === 7 && input.value.startsWith('#')) {
            const color = this.validateAndFormatColor(input.value);
            if (color) {
                this.applyBackgroundColor(color);
                this.updateUI(color);
            }
        }
    }
    /**
     * カラーピッカーの変更イベントハンドラ
     * @param e - イベントオブジェクト
     */
    private onColorPickerInputChange = (e: Event): void => {
        const input = e.target as HTMLInputElement;
        const color = input.value.toUpperCase();
        this.applyBackgroundColor(color);
        this.updateUI(color);
    }

    /**
     * 色の形式を検証します
     * @param color - 検証する色（例: #000000 または 000000）
     * @returns 有効な場合は正規化された色（#XXXXXX形式）、無効な場合はnull
     */
    private validateAndFormatColor(color: string): string | null {
        // スペースを削除
        color = color.trim().toUpperCase();
        // #を削除（ある場合）
        if (color.startsWith('#')) { color = color.substring(1); }
        // 長さチェック
        if (color.length !== 6) { return null; }
        // 16進数チェック
        if (!/^[0-9A-F]{6}$/.test(color)) { return null; }
        return `#${color}`;
    }

    /**
     * 背景色を適用
     * @param color - 色（#XXXXXX形式）
     */
    private applyBackgroundColor(color: string): void {
        // ページの背景色を変更
        if (this.canvasElement) { this.canvasElement.style.backgroundColor = color; }

        // body の背景色を変更
        document.body.style.backgroundColor = color;
    }

    /**
     * UIを更新
     * @param color - 色（#XXXXXX形式）
     */
    private updateUI(color: string): void {
        if (this.colorInputElement) {
            this.colorInputElement.value = color;
            const bgColor = this.getBackgroundColor();
            this.ColorR = parseInt(bgColor.substring(1, 3), 16) / 255.0;
            this.ColorG = parseInt(bgColor.substring(3, 5), 16) / 255.0;
            this.ColorB = parseInt(bgColor.substring(5, 7), 16) / 255.0;
            this.ColorA = 1.0;
        }

        if (this.colorPickerElement) {
            this.colorPickerElement.value = color.toLowerCase();
        }

        if (this.colorValueElement) {
            this.colorValueElement.textContent = color;
        }
    }

    /**
     * 背景色を設定
     * @param color - 色（#XXXXXX形式）
     */
    public setBackgroundColor(color: string): void {
        const validColor = this.validateAndFormatColor(color);
        if (validColor) {
            this.applyBackgroundColor(validColor);
            this.updateUI(validColor);
        } else {
            CubismLogError(`Invalid color format: ${color}`);
        }
    }

    /**
     * 背景色を取得
     * @returns 現在の背景色（#XXXXXX形式）
     */
    public getBackgroundColor(): string {
        return this.colorInputElement?.value || '#FFFFFF';
    }

    public ColorR = 0.0;
    public ColorG = 0.0;
    public ColorB = 0.0;
    public ColorA = 1.0;
}
