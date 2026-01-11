/**
 * Live2D Model UI Controller
 * Provides UI controls for Expressions, Motions, and Parameters
 */

import { LAppDelegate } from './lappdelegate';
import { LAppModel } from './lappmodel';
import * as LAppDefine from './lappdefine';

/**
 * UI Controller for Live2D model manipulation
 */
export class LAppUI {
  private _expressionSelect!: HTMLSelectElement;
  private _motionSelect!: HTMLSelectElement;
  private _parametersContainer!: HTMLDivElement;
  private _controlPanel!: HTMLDivElement;
  private _toggleButton!: HTMLButtonElement;
  private _eyeBlinkToggle!: HTMLInputElement;
  private _breathToggle!: HTMLInputElement;
  private _idleMotionToggle!: HTMLInputElement;
  private _dragFollowToggle!: HTMLInputElement;
  private _parameterSliders: Map<string, HTMLInputElement> = new Map();
  private _parameterValues: Map<string, HTMLSpanElement> = new Map();
  private _manualControlParams: Set<number> = new Set();
  private _manualControlTimers: Map<number, number> = new Map();
  private _updateInterval: number | null = null;
  private _wsStatusText!: HTMLSpanElement;
  private _wsStatusIndicator!: HTMLSpanElement;
  private _wsCheckInterval: number | null = null;

  /**
   * Initialize UI
   */
  public initialize(): void {
    // Get DOM elements
    this._controlPanel = document.getElementById('controlPanel') as HTMLDivElement;
    this._toggleButton = document.getElementById('togglePanel') as HTMLButtonElement;
    this._eyeBlinkToggle = document.getElementById('eyeBlinkToggle') as HTMLInputElement;
    this._breathToggle = document.getElementById('breathToggle') as HTMLInputElement;
    this._idleMotionToggle = document.getElementById('idleMotionToggle') as HTMLInputElement;
    this._dragFollowToggle = document.getElementById('dragFollowToggle') as HTMLInputElement;
    this._expressionSelect = document.getElementById('expressionSelect') as HTMLSelectElement;
    this._motionSelect = document.getElementById('motionSelect') as HTMLSelectElement;
    this._parametersContainer = document.getElementById('parametersContainer') as HTMLDivElement;
    this._wsStatusText = document.getElementById('wsStatusText') as HTMLSpanElement;
    this._wsStatusIndicator = document.getElementById('wsStatusIndicator') as HTMLSpanElement;

    if (!this._controlPanel || !this._toggleButton) {
      console.error('[LAppUI] Required UI elements not found');
      return;
    }

    // Setup toggle button
    this._toggleButton.addEventListener('click', () => {
      this._controlPanel.classList.toggle('hidden');
      this._toggleButton.textContent = this._controlPanel.classList.contains('hidden')
        ? 'Controls'
        : 'Hide';
    });

    // Setup expression select
    this._expressionSelect.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      if (target.value) {
        this.setExpression(target.value);
      }
    });

    // Setup motion select
    this._motionSelect.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      if (target.value) {
        const [group, index] = target.value.split('_');
        this.startMotion(group, parseInt(index));
      }
    });

    // Setup eye blink toggle
    this._eyeBlinkToggle.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.setEyeBlinkEnabled(target.checked);
    });

    // Setup breath toggle
    this._breathToggle.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.setBreathEnabled(target.checked);
    });

    // Setup idle motion toggle
    this._idleMotionToggle.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.setIdleMotionEnabled(target.checked);
    });

    // Setup drag follow toggle
    this._dragFollowToggle.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.setDragFollowEnabled(target.checked);
    });

    // Listen for model loaded events
    window.addEventListener('modelLoaded', () => {
      console.log('[LAppUI] Model loaded, updating UI');
      this.updateUI();
    });

    // Start parameter update loop
    this._updateInterval = window.setInterval(() => {
      this.updateParameterValues();
    }, 100);

    // Start WebSocket status check loop
    this._wsCheckInterval = window.setInterval(() => {
      this.updateWebSocketStatus();
    }, 500);

    // Initial WebSocket status check
    this.updateWebSocketStatus();
  }

  /**
   * Enable or disable eye blink animation
   */
  public setEyeBlinkEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) {
      return;
    }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setEyeBlinkEnabled(enabled);
      console.log(`[LAppUI] Eye blink ${enabled ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Enable or disable breath animation
   */
  public setBreathEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) {
      return;
    }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setBreathEnabled(enabled);
      console.log(`[LAppUI] Breath ${enabled ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Enable or disable idle motion
   */
  public setIdleMotionEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) {
      return;
    }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setIdleMotionEnabled(enabled);
      console.log(`[LAppUI] Idle motion ${enabled ? 'enabled' : 'disabled'}`);
    }
  }
  /**
   * Enable or disable idle motion
   */
  public setDragFollowEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) {
      return;
    }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setDragFollowEnabled(enabled);
      console.log(`[LAppUI] Drag follow ${enabled ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Update UI with current model data
   */
  public updateUI(): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) {
      return;
    }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (!model || !model._modelSetting) {
      return;
    }

    this.updateExpressions(model);
    this.updateMotions(model);
    this.updateParameters(model);

    // Apply current checkbox settings to the new model
    this.applyCheckboxSettings();
  }

  /**
   * Apply current checkbox settings to the model
   */
  private applyCheckboxSettings(): void {
    // Apply eye blink setting
    if (this._eyeBlinkToggle) {
      this.setEyeBlinkEnabled(this._eyeBlinkToggle.checked);
    }

    // Apply breath setting
    if (this._breathToggle) {
      this.setBreathEnabled(this._breathToggle.checked);
    }

    // Apply idle motion setting
    if (this._idleMotionToggle) {
      this.setIdleMotionEnabled(this._idleMotionToggle.checked);
    }

    // Apply drag follow setting
    if (this._dragFollowToggle) {
      this.setDragFollowEnabled(this._dragFollowToggle.checked);
    }
  }

  /**
   * Update expression options
   */
  private updateExpressions(model: LAppModel): void {
    this._expressionSelect.innerHTML = '<option value="">Select Expression...</option>';

    const expressionCount = model._modelSetting.getExpressionCount();

    if (expressionCount > 0) {
      for (let i = 0; i < expressionCount; i++) {
        const name = model._modelSetting.getExpressionName(i);
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        this._expressionSelect.appendChild(option);
      }
    } else {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No expressions available';
      option.disabled = true;
      this._expressionSelect.appendChild(option);
    }
  }

  /**
   * Update motion options
   */
  private updateMotions(model: LAppModel): void {
    this._motionSelect.innerHTML = '<option value="">Select Motion...</option>';

    const motionGroupCount = model._modelSetting.getMotionGroupCount();

    if (motionGroupCount > 0) {
      for (let i = 0; i < motionGroupCount; i++) {
        const groupName = model._modelSetting.getMotionGroupName(i);
        const motionCount = model._modelSetting.getMotionCount(groupName);

        // Create optgroup for each motion group
        const optgroup = document.createElement('optgroup');
        optgroup.label = groupName;

        for (let j = 0; j < motionCount; j++) {
          const option = document.createElement('option');
          option.value = `${groupName}_${j}`;
          option.textContent = `${groupName} ${j}`;
          optgroup.appendChild(option);
        }

        this._motionSelect.appendChild(optgroup);
      }
    } else {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No motions available';
      option.disabled = true;
      this._motionSelect.appendChild(option);
    }
  }

  /**
   * Update parameter sliders
   */
  private updateParameters(model: LAppModel): void {
    this._parametersContainer.innerHTML = '';
    this._parameterSliders.clear();
    this._parameterValues.clear();

    const cubismModel = model.getModel();
    if (!cubismModel) {
      this._parametersContainer.innerHTML = '<div class="empty-message">Model not loaded</div>';
      return;
    }

    const parameterCount = cubismModel.getParameterCount();

    if (parameterCount === 0) {
      this._parametersContainer.innerHTML = '<div class="empty-message">No parameters available</div>';
      return;
    }

    // Get physics parameter names
    const physicsParams = model.getPhysicsParameterNames();

    // Create sliders for each parameter
    for (let i = 0; i < parameterCount; i++) {
      const parameterId = cubismModel.getParameterId(i);
      const parameterName = parameterId.getString().s;
      const minValue = cubismModel.getParameterMinimumValue(i);
      const maxValue = cubismModel.getParameterMaximumValue(i);
      const defaultValue = cubismModel.getParameterDefaultValue(i);
      const currentValue = cubismModel.getParameterValueByIndex(i);

      // Create parameter item container
      const paramItem = document.createElement('div');
      paramItem.className = 'parameter-item';

      // Create label with name and value
      const labelDiv = document.createElement('div');
      labelDiv.className = 'parameter-label';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'param-name';
      nameSpan.textContent = parameterName;

      const valueSpan = document.createElement('span');
      valueSpan.className = 'param-value';
      valueSpan.textContent = currentValue.toFixed(2);
      this._parameterValues.set(parameterName, valueSpan);

      labelDiv.appendChild(nameSpan);
      labelDiv.appendChild(valueSpan);

      // Create slider
      const slider = document.createElement('input');
      slider.type = 'range';
      slider.min = minValue.toString();
      slider.max = maxValue.toString();
      slider.step = '0.01';
      slider.value = currentValue.toString();
      slider.dataset.paramIndex = i.toString();

      // Add physics class if this parameter uses physics
      if (physicsParams.has(parameterName)) {
        slider.classList.add('physics-param');
      }

      slider.addEventListener('input', (e) => {
        const target = e.target as HTMLInputElement;
        const value = parseFloat(target.value);
        const index = parseInt(target.dataset.paramIndex!);

        // Mark this parameter as manually controlled
        this._manualControlParams.add(index);

        // Clear existing timer for this parameter
        const existingTimer = this._manualControlTimers.get(index);
        if (existingTimer) {
          clearTimeout(existingTimer);
        }

        // Set timer to release manual control after 3 seconds
        const timer = window.setTimeout(() => {
          this._manualControlParams.delete(index);
          this._manualControlTimers.delete(index);
        }, 3000);
        this._manualControlTimers.set(index, timer);

        this.setParameter(index, value);

        // Update value display
        const valueDisplay = this._parameterValues.get(parameterName);
        if (valueDisplay) {
          valueDisplay.textContent = value.toFixed(2);
        }
      });

      this._parameterSliders.set(parameterName, slider);

      paramItem.appendChild(labelDiv);
      paramItem.appendChild(slider);
      this._parametersContainer.appendChild(paramItem);
    }
  }

  /**
   * Update parameter value displays
   */
  private updateParameterValues(): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (!model) return;

    const cubismModel = model.getModel();
    if (!cubismModel) return;

    const parameterCount = cubismModel.getParameterCount();

    for (let i = 0; i < parameterCount; i++) {
      const parameterId = cubismModel.getParameterId(i);
      const parameterName = parameterId.getString().s;
      const currentValue = cubismModel.getParameterValueByIndex(i);

      const valueSpan = this._parameterValues.get(parameterName);
      const slider = this._parameterSliders.get(parameterName);

      if (valueSpan) {
        valueSpan.textContent = currentValue.toFixed(2);
      }

      // Update slider position if not being dragged
      if (slider && document.activeElement !== slider) {
        slider.value = currentValue.toString();
      }
    }
  }

  /**
   * Set expression
   */
  private setExpression(expressionId: string): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setExpression(expressionId);
    }
  }

  /**
   * Start motion
   */
  private startMotion(group: string, index: number): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.startMotion(
        group,
        index,
        LAppDefine.PriorityNormal
      );
    }
  }

  /**
   * Set parameter value
   */
  private setParameter(index: number, value: number): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      const cubismModel = model.getModel();
      if (cubismModel) {
        // パラメータ値を設定
        cubismModel.setParameterValueByIndex(index, value);

        // 保存された状態も更新（loadParameters()で上書きされないように）
        cubismModel.saveParameters();

        // モデルに手動制御フラグを設定
        model.setParameterManualControl(index);
      }
    }
  }

  /**
   * Get manual control parameter indices
   */
  public getManualControlParams(): Set<number> {
    return this._manualControlParams;
  }

  /**Update WebSocket connection status display
   */
  private updateWebSocketStatus(): void {
    const delegate = LAppDelegate.getInstance();
    const wsClient = delegate.getWebSocketClient();

    if (!this._wsStatusText || !this._wsStatusIndicator) {
      return;
    }

    if (wsClient && wsClient.isConnected()) {
      this._wsStatusText.textContent = '接続済み';
      this._wsStatusIndicator.style.background = '#4CAF50'; // Green
    } else if (wsClient && wsClient.isRunning()) {
      this._wsStatusText.textContent = '再接続中...';
      this._wsStatusIndicator.style.background = '#FFC107'; // Yellow
    } else {
      this._wsStatusText.textContent = '未接続';
      this._wsStatusIndicator.style.background = '#999'; // Gray
    }
  }

  /**
   * Release resources
   */
  public release(): void {
    if (this._updateInterval !== null) {
      clearInterval(this._updateInterval);
      this._updateInterval = null;
    }
    if (this._wsCheckInterval !== null) {
      clearInterval(this._wsCheckInterval);
      this._wsCheckInterval = null;
    }

    // Clear all manual control timers
    this._manualControlTimers.forEach(timer => clearTimeout(timer));
    this._manualControlTimers.clear();
    this._manualControlParams.clear();

    this._parameterSliders.clear();
    this._parameterValues.clear();
  }

  /**
   * Get instance
   */
  public static getInstance(): LAppUI {
    if (this.s_instance == null) {
      this.s_instance = new LAppUI();
    }

    return this.s_instance;
  }

  /**
   * Release instance
   */
  public static releaseInstance(): void {
    if (this.s_instance != null) {
      this.s_instance.release();
    }

    this.s_instance = null;
  }

  private static s_instance: LAppUI | null = null;
}
