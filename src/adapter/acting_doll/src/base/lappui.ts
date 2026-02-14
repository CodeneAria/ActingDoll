/**
 * Live2D Model UI Controller
 * Provides UI controls for Expressions, Motions, and Parameters
 */

import { LAppDelegate } from './lappdelegate';
import { LAppModel } from './lappmodel';
import * as LAppDefine from './lappdefine';
import {
  CubismLogError,
  CubismLogInfo,
  CubismLogVerbose
} from '@framework/utils/cubismdebug';
import { LAppMultilingual, MessageKey } from './../addons/lappmultilingual';

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
  private _physicsToggle!: HTMLInputElement;
  private _moveUpButton!: HTMLButtonElement;
  private _moveDownButton!: HTMLButtonElement;
  private _moveLeftButton!: HTMLButtonElement;
  private _moveRightButton!: HTMLButtonElement;
  private _resetPositionButton!: HTMLButtonElement;
  private _scaleSlider!: HTMLInputElement;
  private _scaleValue!: HTMLSpanElement;
  private _modelPositionAxis!: HTMLSpanElement;
  private _parameterSliders: Map<string, HTMLInputElement> = new Map();
  private _parameterValues: Map<string, HTMLSpanElement> = new Map();
  private _manualControlParams: Set<number> = new Set();
  private _manualControlTimers: Map<number, number> = new Map();
  private _updateInterval: number | null = null;
  private _wsStatusText!: HTMLSpanElement;
  private _wsStatusIndicator!: HTMLSpanElement;
  private _wsClientId!: HTMLDivElement;
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
    this._physicsToggle = document.getElementById('physicsToggle') as HTMLInputElement;
    this._moveUpButton = document.getElementById('moveUp') as HTMLButtonElement;
    this._moveDownButton = document.getElementById('moveDown') as HTMLButtonElement;
    this._moveLeftButton = document.getElementById('moveLeft') as HTMLButtonElement;
    this._moveRightButton = document.getElementById('moveRight') as HTMLButtonElement;
    this._resetPositionButton = document.getElementById('resetPosition') as HTMLButtonElement;
    this._scaleSlider = document.getElementById('scaleSlider') as HTMLInputElement;
    this._scaleValue = document.getElementById('scaleValue') as HTMLSpanElement;
    this._modelPositionAxis = document.getElementById('modelPositionAxis') as HTMLSpanElement;

    // スケールスライダーの設定
    if (this._scaleSlider) {
      this._scaleSlider.min = LAppDefine.ModelScaleMin.toString();
      this._scaleSlider.max = LAppDefine.ModelScaleMax.toString();
      this._scaleSlider.step = LAppDefine.ModelScaleStep.toString();
    }
    this.updateScaleSlider(LAppDefine.ModelScaleDefault);

    this._expressionSelect = document.getElementById('expressionSelect') as HTMLSelectElement;
    this._motionSelect = document.getElementById('motionSelect') as HTMLSelectElement;
    this._parametersContainer = document.getElementById('parametersContainer') as HTMLDivElement;
    this._wsStatusText = document.getElementById('wsStatusText') as HTMLSpanElement;
    this._wsStatusIndicator = document.getElementById('wsStatusIndicator') as HTMLSpanElement;
    this._wsClientId = document.getElementById('wsClientId') as HTMLDivElement;

    if (!this._controlPanel || !this._toggleButton) {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.UI_ELEMENTS_NOT_FOUND));
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

    // Setup physics toggle
    this._physicsToggle.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.setPhysicsEnabled(target.checked);
    });

    // Setup model position controls
    this._moveUpButton?.addEventListener('click', () => {
      this.moveModel(0, -LAppDefine.ModelPositionMoveStep, true);
    });
    this._moveDownButton?.addEventListener('click', () => {
      this.moveModel(0, LAppDefine.ModelPositionMoveStep, true);
    });
    this._moveLeftButton?.addEventListener('click', () => {
      this.moveModel(-LAppDefine.ModelPositionMoveStep, 0, true);
    });
    this._moveRightButton?.addEventListener('click', () => {
      this.moveModel(LAppDefine.ModelPositionMoveStep, 0, true);
    });
    this._resetPositionButton?.addEventListener('click', () => {
      this.resetModelPosition();
    });

    // Setup scale slider
    this._scaleSlider?.addEventListener('input', (e) => {
      const target = e.target as HTMLInputElement;
      const scale = parseFloat(target.value);
      this.setModelScale(scale);
      if (this._scaleValue) {
        this._scaleValue.textContent = scale.toFixed(1);
      }
    });

    // Listen for model loaded events
    window.addEventListener('modelLoaded', () => {
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_MODEL_LOADED));
      }
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

    // Apply default toggle settings
    this.updateBreathToggle(LAppDefine.DefaultToggle.breath);
    this.updateIdleMotionToggle(LAppDefine.DefaultToggle.idle_motion);
    this.updateDragFollowToggle(LAppDefine.DefaultToggle.drag_follow);
    this.updatePhysicsToggle(LAppDefine.DefaultToggle.physics);
    this.updateEyeBlinkToggle(LAppDefine.DefaultToggle.eye_blink);
  }

  /**
   * Enable or disable eye blink animation
   */
  public setEyeBlinkEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setEyeBlinkEnabled(enabled);
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_EYE_BLINK_TOGGLED, enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
      }
    }

    // Enable or disable eye blink parameter sliders
    this.updateSliderStates();
  }

  /**
   * Enable or disable breath animation
   */
  public setBreathEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setBreathEnabled(enabled);
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_BREATH_TOGGLED, enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
      }
    }

    // Enable or disable breath parameter sliders
    this.updateSliderStates();
  }

  /**
   * Enable or disable idle motion
   */
  public setIdleMotionEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setIdleMotionEnabled(enabled);
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_IDLE_MOTION_TOGGLED, enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
      }
    }
  }
  /**
   * Enable or disable idle motion
   */
  public setDragFollowEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setDragFollowEnabled(enabled);
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_DRAG_FOLLOW_TOGGLED, enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
      }
    }
  }

  /**
   * Enable or disable physics
   */
  public setPhysicsEnabled(enabled: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.setPhysicsEnabled(enabled);
      if (LAppDefine.DebugUILogEnable) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.UI_PHYSICS_TOGGLED, enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
      }
    }

    // Enable or disable physics parameter sliders
    this.updateSliderStates();
  }

  /**
   * Update UI with current model data
   */
  public updateUI(): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) { return; }

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

    // Update slider states based on current toggle states
    this.updateSliderStates();
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
    const breathParams = model.getBreathParameterNames();
    const eyeBlinkParams = model.getEyeBlinkParameterNames();

    // Create sliders for each parameter
    for (let i = 0; i < parameterCount; i++) {
      const parameterId = cubismModel.getParameterId(i);
      const parameterName = parameterId.getString();
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

      // Add classes based on which features affect this parameter
      if (physicsParams.has(parameterName)) {
        slider.classList.add('physics-param');
      }
      if (breathParams.has(parameterName)) {
        slider.classList.add('breath-param');
      }
      if (eyeBlinkParams.has(parameterName)) {
        slider.classList.add('eyeblink-param');
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
      const parameterName = parameterId.getString();
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
      this.updateExpressionSelect(expressionId);
    }
  }

  /**
   * Start motion
   */
  private startMotion(group: string, no: number): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      model.startMotion(group, no, LAppDefine.PriorityNormal);
      this.updateMotionSelect(group, no);
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
        // 一旦保存された状態を読み込み
        cubismModel.loadParameters();
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

      // クライアントIDを表示
      const clientId = wsClient.getClientId();
      if (this._wsClientId && clientId) {
        this._wsClientId.textContent = `クライアントID: ${clientId}`;
      }
    } else if (wsClient && wsClient.isRunning()) {
      this._wsStatusText.textContent = '再接続中...';
      this._wsStatusIndicator.style.background = '#FFC107'; // Yellow
      if (this._wsClientId) {
        this._wsClientId.textContent = 'クライアントID: 取得中...';
      }
    } else {
      this._wsStatusText.textContent = '未接続';
      this._wsStatusIndicator.style.background = '#999'; // Gray
      if (this._wsClientId) {
        this._wsClientId.textContent = 'クライアントID: 取得中...';
      }
    }
  }

  /**
   * Update eye blink toggle checkbox
   */
  public updateEyeBlinkToggle(enabled: boolean): void {
    if (this._eyeBlinkToggle) {
      this._eyeBlinkToggle.checked = enabled;
    }
    this.updateSliderStates();
  }

  /**
   * Update breath toggle checkbox
   */
  public updateBreathToggle(enabled: boolean): void {
    if (this._breathToggle) {
      this._breathToggle.checked = enabled;
    }
    this.updateSliderStates();
  }

  /**
   * Update idle motion toggle checkbox
   */
  public updateIdleMotionToggle(enabled: boolean): void {
    if (this._idleMotionToggle) {
      this._idleMotionToggle.checked = enabled;
    }
  }

  /**
   * Update drag follow toggle checkbox
   */
  public updateDragFollowToggle(enabled: boolean): void {
    if (this._dragFollowToggle) {
      this._dragFollowToggle.checked = enabled;
    }
  }

  /**
   * Update physics toggle checkbox
   */
  public updatePhysicsToggle(enabled: boolean): void {
    if (this._physicsToggle) {
      this._physicsToggle.checked = enabled;
    }
    this.updateSliderStates();
  }

  /**
   * Update slider states based on enabled features
   */
  private updateSliderStates(): void {
    const eyeBlinkEnabled = this._eyeBlinkToggle?.checked ?? false;
    const breathEnabled = this._breathToggle?.checked ?? false;
    const physicsEnabled = this._physicsToggle?.checked ?? false;

    // Update all sliders
    this._parameterSliders.forEach((slider, paramName) => {
      const isEyeBlink = slider.classList.contains('eyeblink-param');
      const isBreath = slider.classList.contains('breath-param');
      const isPhysics = slider.classList.contains('physics-param');

      // Disable slider if any of its controlling features are enabled
      const shouldDisable =
        (isEyeBlink && eyeBlinkEnabled) ||
        (isBreath && breathEnabled) ||
        (isPhysics && physicsEnabled);

      slider.disabled = shouldDisable;

      // Add visual indication
      if (shouldDisable) {
        slider.style.opacity = '0.5';
        //slider.style.cursor = 'not-allowed';
      } else {
        slider.style.opacity = '1';
        //slider.style.cursor = 'pointer';
      }
    });
  }

  /**
   * Update expression select value
   */
  public updateExpressionSelect(expression: string): void {
    if (this._expressionSelect) {
      this._expressionSelect.value = expression;
    }
  }

  /**
   * Update motion select value
   */
  public updateMotionSelect(group: string, index: number): void {
    if (this._motionSelect) {
      this._motionSelect.value = `${group}_${index}`;
    }
  }

  /**
   * Update parameter slider value
   * @param paramName パラメータ名
   * @param value パラメータ値
   */
  public updateParameterSlider(paramName: string, value: number): void {
    const slider = this._parameterSliders.get(paramName);
    const valueSpan = this._parameterValues.get(paramName);

    if (slider) {
      slider.value = value.toString();
    }
    if (valueSpan) {
      valueSpan.textContent = value.toFixed(2);
    }

    // モデルの保持値も更新して手動制御フラグを設定
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const manager = subdelegate.getLive2DManager();
    const model = manager.getModel(0);

    if (model) {
      const cubismModel = model.getModel();
      if (cubismModel) {
        const paramIndex = model.getParameterIndex(paramName);
        if (paramIndex >= 0) {
          // 一旦保存された状態を読み込み
          cubismModel.loadParameters();
          // パラメータ値を設定
          cubismModel.setParameterValueByIndex(paramIndex, value);
          // 保存された状態も更新（loadParameters()で上書きされないように）
          cubismModel.saveParameters();
          // モデルに手動制御フラグを設定
          model.setParameterManualControl(paramIndex);
        }
      }
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
   * モデルの位置を移動
   * @param xValue X方向の移動量
   * @param yValue Y方向の移動量
   * @param isRelative 相対移動かどうか
   */
  public moveModel(xValue: number, yValue: number, isRelative: boolean): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const view = subdelegate.getView();
    if (view) {
      if (isRelative) {
        view.translateRelativeViewMatrix(xValue, yValue);
      } else {
        view.translateViewMatrix(xValue, yValue);
      }
      const viewMatrix = view.getViewMatrix();
      if (viewMatrix) {
        CubismLogVerbose(
          LAppMultilingual.getMessage(MessageKey.UI_MODEL_MOVED,
            viewMatrix.getTranslateX().toFixed(2),
            viewMatrix.getTranslateY().toFixed(2))
        );
        this.updateModelPositionAxis();
      }
    }
  }

  /**
   * モデルの位置表示を更新
   */
  public updateModelPositionAxis(): void {
    if (this._modelPositionAxis) {
      const delegate = LAppDelegate.getInstance();
      const subdelegate = delegate.getSubdelegate(0);
      if (!subdelegate) { return; }
      const view = subdelegate.getView();
      if (view) {
        const viewMatrix = view.getViewMatrix();
        if (viewMatrix) {
          this._modelPositionAxis.textContent =
            `(${viewMatrix.getTranslateX().toFixed(2)},` +
            ` ${viewMatrix.getTranslateY().toFixed(2)})`;
        }
      }
    }
  }

  /**
   * モデルの位置をリセット
   */
  public resetModelPosition(): void {
    const delegate = LAppDelegate.getInstance();
    if (!delegate) { return; }

    const subdelegate = delegate.getSubdelegate(0);
    if (!subdelegate) { return; }

    const view = subdelegate.getView();
    if (view) {
      // 位置リセット
      view.resetViewMatrix();
      // スケールもリセット
      this.updateScaleSlider(LAppDefine.ModelScaleDefault);
      this.updateModelPositionAxis();
    }
  }

  /**
   * スケールスライダーを更新
   * @param scale スケール値
   */
  public updateScaleSlider(scale: number): void {
    if (this._scaleSlider) { this._scaleSlider.value = scale.toString(); }
    if (this._scaleValue) { this._scaleValue.textContent = scale.toFixed(1); }
  }

  /**
   * モデルのスケールを設定
   * @param scale スケール値
   */
  public setModelScale(scale: number): void {
    const delegate = LAppDelegate.getInstance();
    const subdelegate = delegate.getSubdelegate(0);

    if (!subdelegate) return;

    const view = subdelegate.getView();
    if (view) {
      view.setViewScale(scale);
      this.updateScaleSlider(scale);
    }
  }

  /**
   * 現在のスケール値を取得
   * @returns 現在のスケール値
   */
  public getCurrentScale(): number | undefined {
    if (!this._scaleSlider) return undefined;
    return parseFloat(this._scaleSlider.value);
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
