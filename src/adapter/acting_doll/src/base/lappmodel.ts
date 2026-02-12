/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

import { CubismDefaultParameterId_custom } from './../addons/cubismdefaultparameterid_custom';
import { CubismDefaultParameterId } from '@framework/cubismdefaultparameterid';
import { CubismModelSettingJson } from '@framework/cubismmodelsettingjson';
import {
  BreathParameterData,
  CubismBreath
} from '@framework/effect/cubismbreath';
import { CubismEyeBlink } from '@framework/effect/cubismeyeblink';
import { ICubismModelSetting } from '@framework/icubismmodelsetting';
import { CubismIdHandle } from '@framework/id/cubismid';
import { CubismFramework } from '@framework/live2dcubismframework';
import { CubismMatrix44 } from '@framework/math/cubismmatrix44';
import { CubismUserModel } from '@framework/model/cubismusermodel';
import {
  ACubismMotion,
  BeganMotionCallback,
  FinishedMotionCallback
} from '@framework/motion/acubismmotion';
import { CubismMotion } from '@framework/motion/cubismmotion';
import {
  CubismMotionQueueEntryHandle,
  InvalidMotionQueueEntryHandleValue
} from '@framework/motion/cubismmotionqueuemanager';
import { csmRect } from '@framework/type/csmrectf';
import {
  CSM_ASSERT,
  CubismLogDebug,
  CubismLogError,
  CubismLogInfo
} from '@framework/utils/cubismdebug';

import * as LAppDefine from './lappdefine';
import { LAppPal } from './lapppal';
import { TextureInfo } from './lapptexturemanager';
import { LAppWavFileHandler } from './lappwavfilehandler';
import { CubismMoc } from '@framework/model/cubismmoc';
import { LAppDelegate } from './lappdelegate';
import { LAppSubdelegate } from './lappsubdelegate';
import { LAppMultilingual, MessageKey } from './../addons/lappmultilingual';

enum LoadStep {
  LoadAssets,
  LoadModel,
  WaitLoadModel,
  LoadExpression,
  WaitLoadExpression,
  LoadPhysics,
  WaitLoadPhysics,
  LoadPose,
  WaitLoadPose,
  SetupEyeBlink,
  SetupBreath,
  LoadUserData,
  WaitLoadUserData,
  SetupEyeBlinkIds,
  SetupLipSyncIds,
  SetupLayout,
  LoadMotion,
  WaitLoadMotion,
  CompleteInitialize,
  CompleteSetupModel,
  LoadTexture,
  WaitLoadTexture,
  CompleteSetup
}

/**
 * ユーザーが実際に使用するモデルの実装クラス<br>
 * モデル生成、機能コンポーネント生成、更新処理とレンダリングの呼び出しを行う。
 */
export class LAppModel extends CubismUserModel {
  /**
   * model3.jsonが置かれたディレクトリとファイルパスからモデルを生成する
   * @param dir
   * @param fileName
   */
  public loadAssets(dir: string, fileName: string, model_config: LAppDefine.ModelConfig): void {
    this._modelHomeDir = dir;

    fetch(`${this._modelHomeDir}${fileName}`)
      .then(response => response.arrayBuffer())
      .then(arrayBuffer => {
        const setting: ICubismModelSetting = new CubismModelSettingJson(
          arrayBuffer,
          arrayBuffer.byteLength
        );

        // ステートを更新
        this._state = LoadStep.LoadModel;

        // 結果を保存
        this.setupModel(setting);
        if (this._subdelegate) {
          const ui = this._subdelegate.getUI();
          if (ui) {
            ui.resetModelPosition();
            ui.moveModel(model_config.initX, model_config.initY, false);
            ui.setModelScale(model_config.initScale);
            ui.updateModelPositionAxis();
          }
        }
      })
      .catch(error => {
        // model3.json読み込みでエラーが発生した時点で描画は不可能なので、setupせずエラーをcatchして何もしない
        CubismLogError(`Failed to load file ${this._modelHomeDir}${fileName}`);
      });
  }

  /**
   * model3.jsonからモデルを生成する。
   * model3.jsonの記述に従ってモデル生成、モーション、物理演算などのコンポーネント生成を行う。
   *
   * @param setting ICubismModelSettingのインスタンス
   */
  private setupModel(setting: ICubismModelSetting): void {
    this._updating = true;
    this._initialized = false;

    this._modelSetting = setting;

    // CubismModel
    if (this._modelSetting.getModelFileName() != '') {
      const modelFileName = this._modelSetting.getModelFileName();

      fetch(`${this._modelHomeDir}${modelFileName}`)
        .then(response => {
          if (response.ok) {
            return response.arrayBuffer();
          } else if (response.status >= 400) {
            CubismLogError(
              `Failed to load file ${this._modelHomeDir}${modelFileName}`
            );
            return new ArrayBuffer(0);
          }
        })
        .then(arrayBuffer => {
          this.loadModel(arrayBuffer, this._mocConsistency);
          this._state = LoadStep.LoadExpression;

          // callback
          loadCubismExpression();
        });

      this._state = LoadStep.WaitLoadModel;
    } else {
      LAppPal.printMessage('Model data does not exist.');
    }

    // Expression
    const loadCubismExpression = (): void => {
      if (this._modelSetting.getExpressionCount() > 0) {
        const count: number = this._modelSetting.getExpressionCount();

        for (let i = 0; i < count; i++) {
          const expressionName = this._modelSetting.getExpressionName(i);
          const expressionFileName =
            this._modelSetting.getExpressionFileName(i);

          fetch(`${this._modelHomeDir}${expressionFileName}`)
            .then(response => {
              if (response.ok) {
                return response.arrayBuffer();
              } else if (response.status >= 400) {
                CubismLogError(
                  `Failed to load file ${this._modelHomeDir}${expressionFileName}`
                );
                // ファイルが存在しなくてもresponseはnullを返却しないため、空のArrayBufferで対応する
                return new ArrayBuffer(0);
              }
            })
            .then(arrayBuffer => {
              const motion: ACubismMotion = this.loadExpression(
                arrayBuffer,
                arrayBuffer.byteLength,
                expressionName
              );

              if (this._expressions.get(expressionName) != null) {
                ACubismMotion.delete(this._expressions.get(expressionName));
                this._expressions.set(expressionName, null);
              }

              this._expressions.set(expressionName, motion);

              this._expressionCount++;

              if (this._expressionCount >= count) {
                this._state = LoadStep.LoadPhysics;

                // callback
                loadCubismPhysics();
              }
            });
        }
        this._state = LoadStep.WaitLoadExpression;
      } else {
        this._state = LoadStep.LoadPhysics;

        // callback
        loadCubismPhysics();
      }
    };

    // Physics
    const loadCubismPhysics = (): void => {
      if (this._modelSetting.getPhysicsFileName() != '') {
        const physicsFileName = this._modelSetting.getPhysicsFileName();

        fetch(`${this._modelHomeDir}${physicsFileName}`)
          .then(response => {
            if (response.ok) {
              return response.arrayBuffer();
            } else if (response.status >= 400) {
              CubismLogError(
                `Failed to load file ${this._modelHomeDir}${physicsFileName}`
              );
              return new ArrayBuffer(0);
            }
          })
          .then(arrayBuffer => {
            this.loadPhysics(arrayBuffer, arrayBuffer.byteLength);

            this._state = LoadStep.LoadPose;

            // callback
            loadCubismPose();
          });
        this._state = LoadStep.WaitLoadPhysics;
      } else {
        this._state = LoadStep.LoadPose;

        // callback
        loadCubismPose();
      }
    };

    // Pose
    const loadCubismPose = (): void => {
      if (this._modelSetting.getPoseFileName() != '') {
        const poseFileName = this._modelSetting.getPoseFileName();

        fetch(`${this._modelHomeDir}${poseFileName}`)
          .then(response => {
            if (response.ok) {
              return response.arrayBuffer();
            } else if (response.status >= 400) {
              CubismLogError(
                `Failed to load file ${this._modelHomeDir}${poseFileName}`
              );
              return new ArrayBuffer(0);
            }
          })
          .then(arrayBuffer => {
            this.loadPose(arrayBuffer, arrayBuffer.byteLength);

            this._state = LoadStep.SetupEyeBlink;

            // callback
            setupEyeBlink();
          });
        this._state = LoadStep.WaitLoadPose;
      } else {
        this._state = LoadStep.SetupEyeBlink;

        // callback
        setupEyeBlink();
      }
    };

    // EyeBlink
    const setupEyeBlink = (): void => {
      if (this._modelSetting.getEyeBlinkParameterCount() > 0) {
        this._eyeBlink = CubismEyeBlink.create(this._modelSetting);
        this._state = LoadStep.SetupBreath;
      }

      // callback
      setupBreath();
    };

    // Breath
    const setupBreath = (): void => {
      this._breath = CubismBreath.create();

      const parameter_id = CubismFramework.getIdManager().getId(
        this._cubismParameterId.ParamBreath !== undefined ? this._cubismParameterId.ParamBreath : CubismDefaultParameterId.ParamBreath
      );
      const paramIndex = this._model.getParameterIndex(parameter_id);
      const breath_min = this._model.getParameterMinimumValue(paramIndex);
      const breath_max = this._model.getParameterMaximumValue(paramIndex);
      const breath_offset = (breath_min + breath_max) / 2; // 中央値
      const breath_peak = (Math.abs(breath_min) + Math.abs(breath_max)) / 2;
      const breath_cycle = 3.2345;
      const breath_weight = 1;
      const breathParameters: Array<BreathParameterData> = [
        new BreathParameterData(
          parameter_id,   // 呼吸をひもづけるパラメータID
          breath_offset,  // 呼吸を正弦波としたときの、波のオフセット
          breath_peak,    // 呼吸を正弦波としたときの、波の高さ
          breath_cycle,   // 呼吸を正弦波としたときの、波の周期
          breath_weight   // パラメータへの重み
        )
      ];

      this._breath.setParameters(breathParameters);

      // callback
      setupHeadIdle();
    };

    // HeadIdle (アイドリングモーション時の頭の動き)
    const setupHeadIdle = (): void => {
      this._headIdle = CubismBreath.create();
      const headIdleParameters: Array<BreathParameterData> = [
        new BreathParameterData(this._idParamAngleX, 0.0, 15.0, 6.5345, 0.5),
        new BreathParameterData(this._idParamAngleY, 0.0, 8.0, 3.5345, 0.5),
        new BreathParameterData(this._idParamAngleZ, 0.0, 10.0, 5.5345, 0.5),
        new BreathParameterData(this._idParamBodyAngleX, 0.0, 4.0, 15.5345, 0.5)
      ];

      this._headIdle.setParameters(headIdleParameters);
      this._state = LoadStep.LoadUserData;

      // callback
      loadUserData();
    };

    // UserData
    const loadUserData = (): void => {
      if (this._modelSetting.getUserDataFile() != '') {
        const userDataFile = this._modelSetting.getUserDataFile();

        fetch(`${this._modelHomeDir}${userDataFile}`)
          .then(response => {
            if (response.ok) {
              return response.arrayBuffer();
            } else if (response.status >= 400) {
              CubismLogError(
                `Failed to load file ${this._modelHomeDir}${userDataFile}`
              );
              return new ArrayBuffer(0);
            }
          })
          .then(arrayBuffer => {
            this.loadUserData(arrayBuffer, arrayBuffer.byteLength);

            this._state = LoadStep.SetupEyeBlinkIds;

            // callback
            setupEyeBlinkIds();
          });

        this._state = LoadStep.WaitLoadUserData;
      } else {
        this._state = LoadStep.SetupEyeBlinkIds;

        // callback
        setupEyeBlinkIds();
      }
    };

    // EyeBlinkIds
    const setupEyeBlinkIds = (): void => {
      const eyeBlinkIdCount: number =
        this._modelSetting.getEyeBlinkParameterCount();

      this._eyeBlinkIds.length = eyeBlinkIdCount;
      for (let i = 0; i < eyeBlinkIdCount; ++i) {
        this._eyeBlinkIds[i] = this._modelSetting.getEyeBlinkParameterId(i);
      }

      this._state = LoadStep.SetupLipSyncIds;

      // callback
      setupLipSyncIds();
    };

    // LipSyncIds
    const setupLipSyncIds = (): void => {
      const lipSyncIdCount = this._modelSetting.getLipSyncParameterCount();

      this._lipSyncIds.length = lipSyncIdCount;
      for (let i = 0; i < lipSyncIdCount; ++i) {
        this._lipSyncIds[i] = this._modelSetting.getLipSyncParameterId(i);
      }
      this._state = LoadStep.SetupLayout;

      // callback
      setupLayout();
    };

    // Layout
    const setupLayout = (): void => {
      const layout: Map<string, number> = new Map<string, number>();

      if (this._modelSetting == null || this._modelMatrix == null) {
        CubismLogError('Failed to setupLayout().');
        return;
      }

      this._modelSetting.getLayoutMap(layout);
      this._modelMatrix.setupFromLayout(layout);
      this._state = LoadStep.LoadMotion;

      // callback
      loadCubismMotion();
    };

    // Motion
    const loadCubismMotion = (): void => {
      this._state = LoadStep.WaitLoadMotion;
      this._model.saveParameters();
      this._allMotionCount = 0;
      this._motionCount = 0;
      const group: string[] = [];

      const motionGroupCount: number = this._modelSetting.getMotionGroupCount();

      // モーションの総数を求める
      for (let i = 0; i < motionGroupCount; i++) {
        group[i] = this._modelSetting.getMotionGroupName(i);
        this._allMotionCount += this._modelSetting.getMotionCount(group[i]);
      }

      // モーションの読み込み
      for (let i = 0; i < motionGroupCount; i++) {
        this.preLoadMotionGroup(group[i]);
      }

      // モーションがない場合
      if (motionGroupCount == 0) {
        this._state = LoadStep.LoadTexture;

        // 全てのモーションを停止する
        this._motionManager.stopAllMotions();

        this._updating = false;
        this._initialized = true;

        this.createRenderer(
          this._subdelegate.getCanvas().width,
          this._subdelegate.getCanvas().height
        );
        this.setupTextures();
        this.getRenderer().startUp(this._subdelegate.getGlManager().getGl());
        this.getRenderer().loadShaders(LAppDefine.ShaderPath);
      }
    };
  }

  /**
   * テクスチャユニットにテクスチャをロードする
   */
  private setupTextures(): void {
    // iPhoneでのアルファ品質向上のためTypescriptではpremultipliedAlphaを採用
    const usePremultiply = true;

    if (this._state == LoadStep.LoadTexture) {
      // テクスチャ読み込み用
      const textureCount: number = this._modelSetting.getTextureCount();

      for (
        let modelTextureNumber = 0;
        modelTextureNumber < textureCount;
        modelTextureNumber++
      ) {
        // テクスチャ名が空文字だった場合はロード・バインド処理をスキップ
        if (this._modelSetting.getTextureFileName(modelTextureNumber) == '') {
          console.log('getTextureFileName null');
          continue;
        }

        // WebGLのテクスチャユニットにテクスチャをロードする
        let texturePath =
          this._modelSetting.getTextureFileName(modelTextureNumber);
        texturePath = this._modelHomeDir + texturePath;

        // ロード完了時に呼び出すコールバック関数
        const onLoad = (textureInfo: TextureInfo): void => {
          this.getRenderer().bindTexture(modelTextureNumber, textureInfo.id);

          this._textureCount++;

          if (this._textureCount >= textureCount) {
            // ロード完了
            this._state = LoadStep.CompleteSetup;

            // UIを更新
            this.notifyModelLoaded();
          }
        };

        // 読み込み
        this._subdelegate
          .getTextureManager()
          .createTextureFromPngFile(texturePath, usePremultiply, onLoad);
        this.getRenderer().setIsPremultipliedAlpha(usePremultiply);
      }

      this._state = LoadStep.WaitLoadTexture;
    }
  }

  /**
   * レンダラを再構築する
   */
  public reloadRenderer(): void {
    this.deleteRenderer();
    this.createRenderer(
      this._subdelegate.getCanvas().width,
      this._subdelegate.getCanvas().height
    );
    this.setupTextures();
  }

  /**
   * 更新
   */
  public update(): void {
    if (this._state != LoadStep.CompleteSetup) return;

    const deltaTimeSeconds: number = LAppPal.getDeltaTime();
    this._userTimeSeconds += deltaTimeSeconds;

    this._dragManager.update(deltaTimeSeconds);
    this._dragX = this._dragManager.getX();
    this._dragY = this._dragManager.getY();

    // モーションによるパラメータ更新の有無
    let motionUpdated = false;

    //--------------------------------------------------------------------------
    this._model.loadParameters(); // 前回セーブされた状態をロード
    if (this._motionManager.isFinished()) {
      // モーションの再生がない場合、待機モーションの中からランダムで再生する
      if (this._idleMotionEnabled) {
        this.startRandomMotion(
          LAppDefine.MotionGroupIdle,
          LAppDefine.PriorityIdle
        );
      }
    } else {
      motionUpdated = this._motionManager.updateMotion(
        this._model,
        deltaTimeSeconds
      ); // モーションを更新
    }
    this._model.saveParameters(); // 状態を保存
    //--------------------------------------------------------------------------

    // まばたき
    if (!motionUpdated) {
      if (this._eyeBlink != null && this._eyeBlinkEnabled) {
        // メインモーションの更新がないとき
        this._eyeBlink.updateParameters(this._model, deltaTimeSeconds); // 目パチ
      }
    }

    if (this._expressionManager != null) {
      this._expressionManager.updateMotion(this._model, deltaTimeSeconds); // 表情でパラメータ更新（相対変化）
    }

    // ドラッグによる変化
    if (this._dragFollowEnabled) {
      // ドラッグによる顔の向きの調整
      this._model.addParameterValueById(this._idParamAngleX, this._dragX * 30); // -30から30の値を加える
      this._model.addParameterValueById(this._idParamAngleY, this._dragY * 30);
      this._model.addParameterValueById(
        this._idParamAngleZ,
        this._dragX * this._dragY * -30
      );

      // ドラッグによる体の向きの調整
      this._model.addParameterValueById(
        this._idParamBodyAngleX,
        this._dragX * 10
      ); // -10から10の値を加える

      // ドラッグによる目の向きの調整
      this._model.addParameterValueById(this._idParamEyeBallX, this._dragX); // -1から1の値を加える
      this._model.addParameterValueById(this._idParamEyeBallY, this._dragY);
    }

    // 呼吸など
    if (this._breath != null && this._breathEnabled) {
      this._breath.updateParameters(this._model, deltaTimeSeconds);
    }

    // HeadIdle (アイドリングモーションがOnの時のみ)
    if (this._headIdle != null && this._idleMotionEnabled) {
      this._headIdle.updateParameters(this._model, deltaTimeSeconds);
    }

    // 物理演算の設定
    if (this._physics != null && this._physicsEnabled) {
      this._physics.evaluate(this._model, deltaTimeSeconds);
    }

    // リップシンクの設定
    if (this._lipsync) {
      let value = 0.0; // リアルタイムでリップシンクを行う場合、システムから音量を取得して、0~1の範囲で値を入力します。

      this._wavFileHandler.update(deltaTimeSeconds);
      value = this._wavFileHandler.getRms();

      for (let i = 0; i < this._lipSyncIds.length; ++i) {
        this._model.addParameterValueById(this._lipSyncIds[i], value, 0.8);
      }
    }

    // ポーズの設定
    if (this._pose != null) {
      this._pose.updateParameters(this._model, deltaTimeSeconds);
    }

    this._model.update();
  }

  /**
   * 自動目パチを有効/無効にする
   * @param enabled 有効にする場合はtrue、無効にする場合はfalse
   */
  public setEyeBlinkEnabled(enabled: boolean): void {
    this._eyeBlinkEnabled = enabled;
  }
  /**
   * 自動目パチの状態を取得する
   */
  public getEyeBlinkEnabled(): boolean {
    return this._eyeBlinkEnabled;
  }

  /**
   * 呼吸を有効/無効にする
   * @param enabled 有効にする場合はtrue、無効にする場合はfalse
   */
  public setBreathEnabled(enabled: boolean): void {
    this._breathEnabled = enabled;
  }
  /**
   * 呼吸の状態を取得する
   */
  public getBreathEnabled(): boolean {
    return this._breathEnabled;
  }

  /**
   * アイドリングモーションを有効/無効にする
   * @param enabled 有効にする場合はtrue、無効にする場合はfalse
   */
  public setIdleMotionEnabled(enabled: boolean): void {
    this._idleMotionEnabled = enabled;
  }
  /**
   * アイドリングモーションの状態を取得する
   */
  public getIdleMotionEnabled(): boolean {
    return this._idleMotionEnabled;
  }

  /**
   * 物理演算を有効/無効にする
   * @param enabled 有効にする場合はtrue、無効にする場合はfalse
   */
  public setPhysicsEnabled(enabled: boolean): void {
    this._physicsEnabled = enabled;
  }
  /**
   * 物理演算の状態を取得する
   */
  public getPhysicsEnabled(): boolean {
    return this._physicsEnabled;
  }

  /**
   * ドラッグ追従を有効/無効にする
   * @param enabled 有効にする場合はtrue、無効にする場合はfalse
   */
  public setDragFollowEnabled(enabled: boolean): void {
    this._dragFollowEnabled = enabled;
  }
  /**
   * ドラッグ追従の状態を取得する
   */
  public getDragFollowEnabled(): boolean {
    return this._dragFollowEnabled;
  }

  /**
   * パラメータを手動制御中として設定
   * @param paramIndex パラメータインデックス
   */
  public setParameterManualControl(paramIndex: number): void {
    this._manuallyControlledParams.add(paramIndex);
    this._hasManuallyControlledParams = true;
  }

  /**
   * パラメータの手動制御を解除
   * @param paramIndex パラメータインデックス
   */
  public releaseParameterManualControl(paramIndex: number): void {
    this._manuallyControlledParams.delete(paramIndex);
    this._hasManuallyControlledParams = this._manuallyControlledParams.size > 0;
  }

  /**
   * パラメータが手動制御中かチェック
   * @param paramId パラメータID
   */
  private isParameterManuallyControlled(paramId: CubismIdHandle): boolean {
    if (!this._hasManuallyControlledParams) return false;

    const index = this._model.getParameterIndex(paramId);
    return this._manuallyControlledParams.has(index);
  }

  /**
   * 物理演算が適用されているパラメータ名のセットを取得
   * @returns 物理演算が適用されているパラメータ名のセット
   */
  public getPhysicsParameterNames(): Set<string> {
    const physicsParams = new Set<string>();

    if (!this._physics || !this._model) {
      return physicsParams;
    }

    // 物理演算の出力先パラメータを直接取得
    try {
      const outputs = (this._physics as any)._physicsRig?.outputs;
      if (outputs) {
        for (let i = 0; i < outputs.length; i++) {
          const output = outputs[i];
          const paramName = output?.destination?.id?._id;
          if (paramName) {
            physicsParams.add(paramName);
          }
        }
      }
    } catch (e) {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.FAILED_TO_GET_PHYSICS_PARAMS, e));
    }

    return physicsParams;
  }

  /**
   * 呼吸が適用されているパラメータ名のセットを取得
   * @returns 呼吸が適用されているパラメータ名のセット
   */
  public getBreathParameterNames(): Set<string> {
    const breathParams = new Set<string>();

    if (!this._breath || !this._model) {
      return breathParams;
    }

    // 呼吸のパラメータを取得
    try {
      const breathData = (this._breath as any)._breathParameters;
      if (breathData) {
        for (let i = 0; i < breathData.length; i++) {
          const param = breathData[i];
          const paramId = param?.parameterId;
          if (paramId) {
            breathParams.add(paramId.getString());
          }
        }
      }
    } catch (e) {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.FAILED_TO_GET_BREATH_PARAMS, e));
    }

    return breathParams;
  }

  /**
   * 自動目パチが適用されているパラメータ名のセットを取得
   * @returns 自動目パチが適用されているパラメータ名のセット
   */
  public getEyeBlinkParameterNames(): Set<string> {
    const eyeBlinkParams = new Set<string>();

    if (!this._eyeBlink || !this._model) {
      return eyeBlinkParams;
    }

    // 目パチのパラメータIDを取得
    for (let i = 0; i < this._eyeBlinkIds.length; i++) {
      const paramId = this._eyeBlinkIds[i];
      eyeBlinkParams.add(paramId.getString());
    }

    return eyeBlinkParams;
  }

  /**
   * 引数で指定したモーションの再生を開始する
   * @param group モーショングループ名
   * @param no グループ内の番号
   * @param priority 優先度
   * @param onFinishedMotionHandler モーション再生終了時に呼び出されるコールバック関数
   * @return 開始したモーションの識別番号を返す。個別のモーションが終了したか否かを判定するisFinished()の引数で使用する。開始できない時は[-1]
   */
  public startMotion(
    group: string,
    no: number,
    priority: number,
    onFinishedMotionHandler?: FinishedMotionCallback,
    onBeganMotionHandler?: BeganMotionCallback
  ): CubismMotionQueueEntryHandle {
    if (priority == LAppDefine.PriorityForce) {
      this._motionManager.setReservePriority(priority);
    } else if (!this._motionManager.reserveMotion(priority)) {
      if (this._debugMode) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.CANT_START_MOTION));
      }
      return InvalidMotionQueueEntryHandleValue;
    }
    if (no < 0 || no >= this._modelSetting.getMotionCount(group)) {
      CubismLogDebug(LAppMultilingual.getMessage(MessageKey.CANT_MOTION_NO_OVERFLOW, no));
      return InvalidMotionQueueEntryHandleValue;
    } else {
      const motionFileName = this._modelSetting.getMotionFileName(group, no);

      // ex) idle_0
      const name = `${group}_${no}`;
      let motion: CubismMotion = this._motions.get(name) as CubismMotion;
      let autoDelete = false;

      CubismLogDebug(LAppMultilingual.getMessage(MessageKey.START_MOTION, group, `${no}`));
      if (motion == null) {
        fetch(`${this._modelHomeDir}${motionFileName}`)
          .then(response => {
            if (response.ok) {
              return response.arrayBuffer();
            } else if (response.status >= 400) {
              CubismLogError(LAppMultilingual.getMessage(MessageKey.FAILED_TO_LOAD_FILE, `${this._modelHomeDir}${motionFileName}`));
              return new ArrayBuffer(0);
            }
          })
          .then(arrayBuffer => {
            motion = this.loadMotion(
              arrayBuffer,
              arrayBuffer.byteLength,
              null,
              onFinishedMotionHandler,
              onBeganMotionHandler,
              this._modelSetting,
              group,
              no,
              this._motionConsistency
            );
          });

        if (motion) {
          motion.setEffectIds(this._eyeBlinkIds, this._lipSyncIds);
          autoDelete = true; // 終了時にメモリから削除
        } else {
          CubismLogError(LAppMultilingual.getMessage(MessageKey.CANT_START_MOTION_FILE, motionFileName));
          // ロードできなかったモーションのReservePriorityをリセットする
          this._motionManager.setReservePriority(LAppDefine.PriorityNone);
          return InvalidMotionQueueEntryHandleValue;
        }
      } else {
        motion.setBeganMotionHandler(onBeganMotionHandler);
        motion.setFinishedMotionHandler(onFinishedMotionHandler);
      }
      // 現在のモーション情報を保存
      this._currentMotionGroup = group;
      this._currentMotionNo = no;

      //voice
      const voice = this._modelSetting.getMotionSoundFileName(group, no);
      if (voice.localeCompare('') != 0) {
        let path = voice;
        path = this._modelHomeDir + path;
        this._wavFileHandler.start(path);
      }

      if (this._debugMode) {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.START_MOTION, group, no));
      }
      // Update UI select
      if (this._subdelegate) {
        const ui = this._subdelegate.getUI();
        if (ui) {
          ui.updateMotionSelect(group, no);
        }
      }

      return this._motionManager.startMotionPriority(
        motion,
        autoDelete,
        priority
      );
    }
  }

  /**
   * ランダムに選ばれたモーションの再生を開始する。
   * @param group モーショングループ名
   * @param priority 優先度
   * @param onFinishedMotionHandler モーション再生終了時に呼び出されるコールバック関数
   * @return 開始したモーションの識別番号を返す。個別のモーションが終了したか否かを判定するisFinished()の引数で使用する。開始できない時は[-1]
   */
  public startRandomMotion(
    group: string,
    priority: number,
    onFinishedMotionHandler?: FinishedMotionCallback,
    onBeganMotionHandler?: BeganMotionCallback
  ): CubismMotionQueueEntryHandle {
    if (this._modelSetting.getMotionCount(group) == 0) {
      return InvalidMotionQueueEntryHandleValue;
    }

    const no: number = Math.floor(
      Math.random() * this._modelSetting.getMotionCount(group)
    );

    return this.startMotion(
      group,
      no,
      priority,
      onFinishedMotionHandler,
      onBeganMotionHandler
    );
  }

  /**
   * 引数で指定した表情モーションをセットする
   *
   * @param expressionId 表情モーションのID
   */
  public setExpression(expressionId: string): string {
    const motion: ACubismMotion = this._expressions.get(expressionId);

    if (this._debugMode) {
      LAppPal.printMessage(`[APP]expression: [${expressionId}]`);
    }

    if (motion != null) {
      this._expressionManager.startMotion(motion, false);
      this._currentExpressionId = expressionId;

      // Update UI select
      if (this._subdelegate) {
        const ui = this._subdelegate.getUI();
        if (ui) {
          ui.updateExpressionSelect(expressionId);
        }
      }
    } else {
      if (this._debugMode) {
        LAppPal.printMessage(`[APP]expression[${expressionId}] is null`);
      }
    }
    return this._currentExpressionId;
  }

  /**
   * 現在設定されている表情IDを取得する
   * @returns 現在の表情ID（設定されていない場合はnull）
   */
  public getCurrentExpression(): string | null {
    return this._currentExpressionId;
  }

  /**
   * 現在再生中のモーション情報を取得する
   * @returns 現在のモーション情報（グループ名と番号）。再生中でない場合はnull
   */
  public getCurrentMotion(): { group: string; no: number; priority: number } | null {
    if (this._currentMotionGroup !== null && this._currentMotionNo !== null) {
      return {
        group: this._currentMotionGroup,
        no: this._currentMotionNo,
        priority: this._motionManager.getCurrentPriority()
      };
    }
    return null;
  }

  /**
   * ランダムに選ばれた表情モーションをセットする
   */
  public setRandomExpression(): void {
    if (this._expressions.size == 0) {
      return;
    }

    const no: number = Math.floor(Math.random() * this._expressions.size);

    for (let i = 0; i < this._expressions.size; i++) {
      if (i == no) {
        // const name: string = this._expressions._keyValues[i].first;
        const expressionsArray = [...this._expressions.entries()];
        const name: string = expressionsArray[i][0];
        this.setExpression(name);
        CubismLogDebug(LAppMultilingual.getMessage(MessageKey.EXPRESSION_SET, name));
        return;
      }
    }
  }

  /**
   * ArrayBufferからWavファイルを読み込んでリップシンク開始
   * @param arrayBuffer Wavファイルのバイナリデータ
   * @param length データ長
   */
  public loadWavFileFromBuffer(arrayBuffer: ArrayBuffer, length: number): void {
    if (!this._wavFileHandler) {
      CubismLogError('WavFileHandler is not initialized');
      return;
    }
    this._wavFileHandler.run(arrayBuffer, length);
    //this._lipsync = true;
  }

  public getModelName(): string {
    if (this._modelSetting.getModelFileName() != '') {
      const modelFileName = this._modelSetting.getModelFileName();
      // 拡張子を削除
      const lastDotIndex = modelFileName.lastIndexOf('.');
      if (lastDotIndex > 0) {
        return modelFileName.substring(0, lastDotIndex);
      }
      return modelFileName;
    } else {
      return LAppMultilingual.getMessage(MessageKey.UNKNOWN);
    }
  }

  /**
   * パラメータ名からインデックスを取得
   * @param paramName パラメータ名（文字列）
   * @returns パラメータインデックス。見つからない場合は-1
   */
  public getParameterIndex(paramName: string): number {
    if (!this._model) {
      return -1;
    }
    const paramId = CubismFramework.getIdManager().getId(paramName);
    const index = this._model.getParameterIndex(paramId);
    // パラメータが存在しない場合は-1を返す
    if (index < 0 || index >= this._model.getParameterCount()) {
      return -1;
    }
    return index;
  }

  /**
   * インデックスでパラメータ値を設定
   * @param paramIndex パラメータインデックス
   * @param value 設定する値
   */
  public setParameterValueByIndex(paramIndex: number, value: number): void {
    if (!this._model || paramIndex < 0) {
      return;
    }
    this._model.setParameterValueByIndex(paramIndex, value);
  }

  /**
   * イベントの発火を受け取る
   */
  public motionEventFired(eventValue: string): void {
    CubismLogInfo('{0} is fired on LAppModel!!', eventValue);
  }

  /**
   * 当たり判定テスト
   * 指定ＩＤの頂点リストから矩形を計算し、座標をが矩形範囲内か判定する。
   *
   * @param hitArenaName  当たり判定をテストする対象のID
   * @param x             判定を行うX座標
   * @param y             判定を行うY座標
   */
  public hitTest(hitArenaName: string, x: number, y: number): boolean {
    // 透明時は当たり判定無し。
    if (this._opacity < 1) {
      return false;
    }

    // モデルセッティングが無い、またはHitAreasが定義されていない場合
    if (this._modelSetting == null) {
      return false;
    }

    const count: number = this._modelSetting.getHitAreasCount();

    for (let i = 0; i < count; i++) {
      if (this._modelSetting.getHitAreaName(i) == hitArenaName) {
        const drawId: CubismIdHandle = this._modelSetting.getHitAreaId(i);
        if (this.isHit(drawId, x, y)) {
          // WebSocketでサーバーに通知（LAppDelegateから取得）
          const websocketClient = LAppDelegate.getInstance().getWebSocketClient();
          if (websocketClient) {
            websocketClient.sendModelHit(
              this._modelSetting.getModelFileName(), drawId.getString(), x, y
            );
          }
          return true;
        }
      }
    }

    return false;
  }

  /**
   * モーションデータをグループ名から一括でロードする。
   * モーションデータの名前は内部でModelSettingから取得する。
   *
   * @param group モーションデータのグループ名
   */
  public preLoadMotionGroup(group: string): void {
    for (let i = 0; i < this._modelSetting.getMotionCount(group); i++) {
      const motionFileName = this._modelSetting.getMotionFileName(group, i);

      // ex) idle_0
      const name = `${group}_${i}`;
      if (this._debugMode) {
        CubismLogInfo(
          `[APP]load motion: ${motionFileName} => [${name}]`
        );
      }

      fetch(`${this._modelHomeDir}${motionFileName}`)
        .then(response => {
          if (response.ok) {
            return response.arrayBuffer();
          } else if (response.status >= 400) {
            CubismLogError(
              `Failed to load file ${this._modelHomeDir}${motionFileName}`
            );
            return new ArrayBuffer(0);
          }
        })
        .then(arrayBuffer => {
          const tmpMotion: CubismMotion = this.loadMotion(
            arrayBuffer,
            arrayBuffer.byteLength,
            name,
            null,
            null,
            this._modelSetting,
            group,
            i,
            this._motionConsistency
          );

          if (tmpMotion != null) {
            tmpMotion.setEffectIds(this._eyeBlinkIds, this._lipSyncIds);

            if (this._motions.get(name) != null) {
              ACubismMotion.delete(this._motions.get(name));
            }

            this._motions.set(name, tmpMotion);

            this._motionCount++;
          } else {
            // loadMotionできなかった場合はモーションの総数がずれるので1つ減らす
            this._allMotionCount--;
          }

          if (this._motionCount >= this._allMotionCount) {
            this._state = LoadStep.LoadTexture;

            // 全てのモーションを停止する
            this._motionManager.stopAllMotions();

            this._updating = false;
            this._initialized = true;

            this.createRenderer(
              this._subdelegate.getCanvas().width,
              this._subdelegate.getCanvas().height
            );
            this.setupTextures();
            this.getRenderer().startUp(
              this._subdelegate.getGlManager().getGl()
            );
            this.getRenderer().loadShaders(LAppDefine.ShaderPath);
          }
        });
    }
  }

  /**
   * すべてのモーションデータを解放する。
   */
  public releaseMotions(): void {
    this._motions.clear();
  }

  /**
   * 全ての表情データを解放する。
   */
  public releaseExpressions(): void {
    this._expressions.clear();
  }

  /**
   * モデルを描画する処理。モデルを描画する空間のView-Projection行列を渡す。
   */
  public doDraw(): void {
    if (this._model == null) return;

    // キャンバスサイズを渡す
    const canvas = this._subdelegate.getCanvas();
    const viewport: number[] = [0, 0, canvas.width, canvas.height];

    this.getRenderer().setRenderState(
      this._subdelegate.getFrameBuffer(),
      viewport
    );
    this.getRenderer().drawModel(LAppDefine.ShaderPath);
  }

  /**
   * モデルを描画する処理。モデルを描画する空間のView-Projection行列を渡す。
   */
  public draw(matrix: CubismMatrix44): void {
    if (this._model == null) {
      return;
    }

    // 各読み込み終了後
    if (this._state == LoadStep.CompleteSetup) {
      matrix.multiplyByMatrix(this._modelMatrix);

      this.getRenderer().setMvpMatrix(matrix);

      this.doDraw();
    }
  }

  public async hasMocConsistencyFromFile() {
    CSM_ASSERT(this._modelSetting.getModelFileName().localeCompare(``));

    // CubismModel
    if (this._modelSetting.getModelFileName() != '') {
      const modelFileName = this._modelSetting.getModelFileName();

      const response = await fetch(`${this._modelHomeDir}${modelFileName}`);
      const arrayBuffer = await response.arrayBuffer();

      this._consistency = CubismMoc.hasMocConsistency(arrayBuffer);

      if (!this._consistency) {
        CubismLogInfo('Inconsistent MOC3.');
      } else {
        CubismLogInfo('Consistent MOC3.');
      }

      return this._consistency;
    } else {
      LAppPal.printMessage('Model data does not exist.');
    }
  }

  public setSubdelegate(subdelegate: LAppSubdelegate): void {
    this._subdelegate = subdelegate;
  }

  /**
   * モデル読み込み完了時の通知
   */
  private notifyModelLoaded(): void {
    // UIを更新するためのイベントを発火
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('modelLoaded');
      window.dispatchEvent(event);
    }
  }

  /**
   * コンストラクタ
   */
  public constructor(is_custom: boolean) {
    super();

    this._modelSetting = null;
    this._modelHomeDir = null;
    this._userTimeSeconds = 0.0;

    this._eyeBlinkIds = new Array<CubismIdHandle>();
    this._lipSyncIds = new Array<CubismIdHandle>();

    this._motions = new Map<string, ACubismMotion>();
    this._expressions = new Map<string, ACubismMotion>();
    this._currentExpressionId = null;
    this._currentMotionGroup = null;
    this._currentMotionNo = null;

    this._hitArea = new Array<csmRect>();
    this._userArea = new Array<csmRect>();

    if (is_custom) {
      this._cubismParameterId = CubismDefaultParameterId_custom;
    } else {
      this._cubismParameterId = CubismDefaultParameterId;
    }
    this._idParamAngleX = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamAngleX !== undefined ? this._cubismParameterId.ParamAngleX : CubismDefaultParameterId.ParamAngleX
    );
    this._idParamAngleY = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamAngleY !== undefined ? this._cubismParameterId.ParamAngleY : CubismDefaultParameterId.ParamAngleY
    );
    this._idParamAngleZ = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamAngleZ !== undefined ? this._cubismParameterId.ParamAngleZ : CubismDefaultParameterId.ParamAngleZ
    );
    this._idParamEyeBallX = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamEyeBallX !== undefined ? this._cubismParameterId.ParamEyeBallX : CubismDefaultParameterId.ParamEyeBallX
    );
    this._idParamEyeBallY = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamEyeBallY !== undefined ? this._cubismParameterId.ParamEyeBallY : CubismDefaultParameterId.ParamEyeBallY
    );
    this._idParamBodyAngleX = CubismFramework.getIdManager().getId(
      this._cubismParameterId.ParamBodyAngleX !== undefined ? this._cubismParameterId.ParamBodyAngleX : CubismDefaultParameterId.ParamBodyAngleX
    );

    if (LAppDefine.MOCConsistencyValidationEnable) {
      this._mocConsistency = true;
    }

    if (LAppDefine.MotionConsistencyValidationEnable) {
      this._motionConsistency = true;
    }

    this._state = LoadStep.LoadAssets;
    this._expressionCount = 0;
    this._textureCount = 0;
    this._motionCount = 0;
    this._allMotionCount = 0;
    this._wavFileHandler = new LAppWavFileHandler();
    this._consistency = false;
  }

  private _subdelegate: LAppSubdelegate;

  _modelSetting: ICubismModelSetting; // モデルセッティング情報
  _modelHomeDir: string; // モデルセッティングが置かれたディレクトリ
  _userTimeSeconds: number; // デルタ時間の積算値[秒]

  _eyeBlinkIds: Array<CubismIdHandle>; // モデルに設定された瞬き機能用パラメータID
  _eyeBlinkEnabled: boolean = true; // 自動目パチの有効/無効
  _breathEnabled: boolean = true; // 呼吸の有効/無効
  _idleMotionEnabled: boolean = false; // アイドリングモーションの有効/無効
  _dragFollowEnabled: boolean = false; // ドラッグ追従の有効/無効
  _physicsEnabled: boolean = true; // 物理演算の有効/無効
  _manuallyControlledParams: Set<number> = new Set(); // 手動制御中のパラメータインデックス
  _hasManuallyControlledParams: boolean = false; // 手動制御中のパラメータがあるか
  _lipSyncIds: Array<CubismIdHandle>; // モデルに設定されたリップシンク機能用パラメータID

  _motions: Map<string, ACubismMotion>; // 読み込まれているモーションのリスト
  _expressions: Map<string, ACubismMotion>; // 読み込まれている表情のリスト
  _currentExpressionId: string | null; // 現在設定されている表情ID
  _currentMotionGroup: string | null; // 現在再生中のモーショングループ名
  _currentMotionNo: number | null; // 現在再生中のモーション番号

  _hitArea: Array<csmRect>;
  _userArea: Array<csmRect>;

  _idParamAngleX: CubismIdHandle; // パラメータID: ParamAngleX
  _idParamAngleY: CubismIdHandle; // パラメータID: ParamAngleY
  _idParamAngleZ: CubismIdHandle; // パラメータID: ParamAngleZ
  _idParamEyeBallX: CubismIdHandle; // パラメータID: ParamEyeBallX
  _idParamEyeBallY: CubismIdHandle; // パラメータID: ParamEyeBAllY
  _idParamBodyAngleX: CubismIdHandle; // パラメータID: ParamBodyAngleX

  _state: LoadStep; // 現在のステータス管理用
  _expressionCount: number; // 表情データカウント
  _textureCount: number; // テクスチャカウント
  _motionCount: number; // モーションデータカウント
  _allMotionCount: number; // モーション総数
  _wavFileHandler: LAppWavFileHandler; //wavファイルハンドラ
  _consistency: boolean; // MOC3整合性チェック管理用
  _cubismParameterId: any; // デフォルトパラメータID
  _headIdle: CubismBreath; // 頭部アイドルモーション
}
