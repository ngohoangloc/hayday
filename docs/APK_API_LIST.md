# Danh sách API — Hay Day (com.supercell.hayday)

| Mục | Giá trị |
|---|---|
| Package | `com.supercell.hayday` |
| Phiên bản | 1.73.89 (versionCode 2229) |
| SDK | min 32 / target 36 (Android 12L+ / compile 36) |
| Kích thước cài đặt | ~853 MB (base 63.6MB + native 57.5MB + asset pack 692MB) |
| Main activity | `com.supercell.hayday.GameApp` |

## 1. Quyền Android yêu cầu (24)

- `android.permission.ACCESS_ADSERVICES_AD_ID`
- `android.permission.ACCESS_ADSERVICES_ATTRIBUTION`
- `android.permission.ACCESS_ADSERVICES_TOPICS`
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.ACCESS_WIFI_STATE`
- `android.permission.CHANGE_WIFI_STATE`
- `android.permission.FOREGROUND_SERVICE`
- `android.permission.INTERNET`
- `android.permission.POST_NOTIFICATIONS`
- `android.permission.READ_BASIC_PHONE_STATE`
- `android.permission.USE_BIOMETRIC`
- `android.permission.USE_FINGERPRINT`
- `android.permission.VIBRATE`
- `android.permission.WAKE_LOCK`
- `com.android.vending.BILLING`
- `com.android.vending.CHECK_LICENSE`
- `com.google.android.c2dm.permission.RECEIVE`
- `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE`
- `com.google.android.gms.permission.AD_ID`
- `com.google.android.providers.gsf.permission.READ_GSERVICES`
- `com.huawei.appmarket.service.commondata.permission.GET_COMMON_DATA`
- `com.samsung.android.mapsagent.permission.READ_APP_INFO`
- `com.supercell.hayday.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
- `com.supercell.id.SHARED_DATA_ACCESS`

Nhóm ý nghĩa: mạng (INTERNET, NETWORK/WIFI STATE), thông báo (POST_NOTIFICATIONS),
sinh trắc học (USE_BIOMETRIC/FINGERPRINT — dùng cho SuperCell ID), thanh toán
(BILLING, CHECK_LICENSE), Firebase push (c2dm), đo lường quảng cáo (AD_ID,
ADSERVICES_*), wake/vibrate cho thông báo trong game.

## 2. Component (API surface) — 57 activities, 18 services, 16 receivers, 16 providers

### Services
- `androidx.camera.core.impl.MetadataHolderService`
- `androidx.credentials.playservices.CredentialProviderMetadataHolder`
- `androidx.room.MultiInstanceInvalidationService`
- `androidx.work.impl.background.systemalarm.SystemAlarmService`
- `androidx.work.impl.background.systemjob.SystemJobService`
- `androidx.work.impl.foreground.SystemForegroundService`
- `com.applovin.impl.adview.activity.FullscreenAdService`
- `com.google.android.datatransport.runtime.backends.TransportBackendDiscovery`
- `com.google.android.datatransport.runtime.scheduling.jobscheduling.JobInfoSchedulerService`
- `com.google.android.gms.ads.AdService`
- `com.google.android.gms.analytics.AnalyticsJobService`
- `com.google.android.gms.analytics.AnalyticsService`
- `com.google.android.gms.auth.api.signin.RevocationBoundService`
- `com.google.android.gms.measurement.AppMeasurementJobService`
- `com.google.android.gms.measurement.AppMeasurementService`
- `com.google.firebase.components.ComponentDiscoveryService`
- `com.google.firebase.messaging.FirebaseMessagingService`
- `com.supercell.titan.PushMessageService`

### Receivers
- `androidx.profileinstaller.ProfileInstallReceiver`
- `androidx.work.impl.background.systemalarm.ConstraintProxy$BatteryChargingProxy`
- `androidx.work.impl.background.systemalarm.ConstraintProxy$BatteryNotLowProxy`
- `androidx.work.impl.background.systemalarm.ConstraintProxy$NetworkStateProxy`
- `androidx.work.impl.background.systemalarm.ConstraintProxy$StorageNotLowProxy`
- `androidx.work.impl.background.systemalarm.ConstraintProxyUpdateReceiver`
- `androidx.work.impl.background.systemalarm.RescheduleReceiver`
- `androidx.work.impl.diagnostics.DiagnosticsReceiver`
- `androidx.work.impl.utils.ForceStopRunnable$BroadcastReceiver`
- `com.google.android.datatransport.runtime.scheduling.jobscheduling.AlarmManagerSchedulerBroadcastReceiver`
- `com.google.android.gms.analytics.AnalyticsReceiver`
- `com.google.android.gms.measurement.AppMeasurementReceiver`
- `com.google.firebase.iid.FirebaseInstanceIdReceiver`
- `com.pichillilorenzo.flutter_inappwebview_android.chrome_custom_tabs.ActionBroadcastReceiver`
- `com.supercell.titan.TimeAlarm`
- `dev.fluttercommunity.plus.share.SharePlusPendingIntent`

### Providers
- `androidx.startup.InitializationProvider`
- `com.applovin.sdk.AppLovinInitProvider`
- `com.facebook.ads.AudienceNetworkContentProvider`
- `com.google.android.gms.ads.MobileAdsInitProvider`
- `com.google.android.gms.games.provider.PlayGamesInitProvider`
- `com.google.firebase.provider.FirebaseInitProvider`
- `com.ironsource.lifecycle.IronsourceLifecycleProvider`
- `com.ironsource.lifecycle.LevelPlayActivityLifecycleProvider`
- `com.supercell.id.scid_plugin.platform_interface.SharedDataContentProvider`
- `com.supercell.titan.NativeSharingFileProvider`
- `com.supercell.titan.imagesharing.ImageSharingFileProvider`
- `com.vungle.ads.VungleProvider`
- `dev.fluttercommunity.plus.share.ShareFileProvider`
- `io.sentry.android.core.SentryInitProvider`
- `io.sentry.android.core.SentryPerformanceProvider`
- `io.sentry.ndk.SentryNdkPreloadProvider`

### Activities (đầy đủ)
- `androidx.credentials.playservices.HiddenActivity`
- `androidx.credentials.playservices.IdentityCredentialApiHiddenActivity`
- `com.android.billingclient.api.ProxyBillingActivity`
- `com.android.billingclient.api.ProxyBillingActivityV2`
- `com.applovin.adview.AppLovinConfirmationActivity`
- `com.applovin.adview.AppLovinFullscreenActivity`
- `com.applovin.adview.AppLovinFullscreenImmersiveActivity`
- `com.applovin.adview.AppLovinInterstitialActivity`
- `com.applovin.creative.MaxCreativeDebuggerActivity`
- `com.applovin.creative.MaxCreativeDebuggerDisplayedAdActivity`
- `com.applovin.mediation.MaxDebuggerActivity`
- `com.applovin.mediation.MaxDebuggerAdUnitDetailActivity`
- `com.applovin.mediation.MaxDebuggerAdUnitWaterfallsListActivity`
- `com.applovin.mediation.MaxDebuggerAdUnitsListActivity`
- `com.applovin.mediation.MaxDebuggerCmpNetworksListActivity`
- `com.applovin.mediation.MaxDebuggerDetailActivity`
- `com.applovin.mediation.MaxDebuggerMultiAdActivity`
- `com.applovin.mediation.MaxDebuggerTcfConsentStatusesListActivity`
- `com.applovin.mediation.MaxDebuggerTcfInfoListActivity`
- `com.applovin.mediation.MaxDebuggerTcfStringActivity`
- `com.applovin.mediation.MaxDebuggerTestLiveNetworkActivity`
- `com.applovin.mediation.MaxDebuggerTestModeNetworkActivity`
- `com.applovin.mediation.MaxDebuggerUnifiedFlowActivity`
- `com.applovin.mediation.MaxDebuggerWaterfallSegmentsActivity`
- `com.applovin.sdk.AppLovinWebViewActivity`
- `com.facebook.ads.AudienceNetworkActivity`
- `com.google.android.gms.ads.AdActivity`
- `com.google.android.gms.ads.NotificationHandlerActivity`
- `com.google.android.gms.ads.OutOfContextTestingActivity`
- `com.google.android.gms.auth.api.signin.internal.SignInHubActivity`
- `com.google.android.gms.common.api.GoogleApiActivity`
- `com.google.android.gms.games.internal.v2.resolution.GamesResolutionActivity`
- `com.google.android.play.core.common.PlayCoreDialogWrapperActivity`
- `com.helpshift.activities.HSDebugActivity`
- `com.helpshift.activities.HSMainActivity`
- `com.ironsource.mediationsdk.testSuite.TestSuiteActivity`
- `com.ironsource.sdk.controller.ControllerActivity`
- `com.ironsource.sdk.controller.InterstitialActivity`
- `com.ironsource.sdk.controller.OpenUrlActivity`
- `com.moloco.sdk.xenoss.sdkdevkit.android.adrenderer.internal.mraid.MraidActivity`
- `com.moloco.sdk.xenoss.sdkdevkit.android.adrenderer.internal.staticrenderer.StaticAdActivity`
- `com.moloco.sdk.xenoss.sdkdevkit.android.adrenderer.internal.templates.renderer.fullscreen.FullscreenWebviewActivity`
- `com.moloco.sdk.xenoss.sdkdevkit.android.adrenderer.internal.vast.VastActivity`
- `com.pichillilorenzo.flutter_inappwebview_android.chrome_custom_tabs.ChromeCustomTabsActivity`
- `com.pichillilorenzo.flutter_inappwebview_android.chrome_custom_tabs.ChromeCustomTabsActivitySingleInstance`
- `com.pichillilorenzo.flutter_inappwebview_android.chrome_custom_tabs.TrustedWebActivity`
- `com.pichillilorenzo.flutter_inappwebview_android.chrome_custom_tabs.TrustedWebActivitySingleInstance`
- `com.pichillilorenzo.flutter_inappwebview_android.in_app_browser.InAppBrowserActivity`
- `com.supercell.hayday.GameApp`
- `com.unity3d.ads.adplayer.FullScreenWebViewDisplay`
- `com.unity3d.ironsourceads.internal.services.InlineStoreActivity`
- `com.unity3d.services.ads.adunit.AdUnitActivity`
- `com.unity3d.services.ads.adunit.AdUnitSoftwareActivity`
- `com.unity3d.services.ads.adunit.AdUnitTransparentActivity`
- `com.unity3d.services.ads.adunit.AdUnitTransparentSoftwareActivity`
- `com.vungle.ads.internal.ui.VungleActivity`
- `io.flutter.plugins.urllauncher.WebViewActivity`

## 3. Thư viện native (0 file, arm64-v8a)


Game engine: **Flutter** (libflutter.so + libapp.so Dart AOT) + engine riêng của
Supercell (`libsupercell_hayday.so`, `libscid_sdk.so` — Supercell ID) + FMOD audio
(`libfmod.so`, `libfmodstudio.so`), Sentry crash reporting, Quago fraud detection.

## 4. SDK third-party nhận diện

- applovin
- facebook
- firebase
- google
- helpshift
- ironsource
- play
- supercell
- unity
- vungle

Chi tiết: Firebase (push/analytics), Google Play Games & Billing & Ads (AdMob),
AppLovin + IronSource/LevelPlay + Vungle (quảng cáo), Facebook SDK, Helpshift
(hỗ trợ trong game), Sentry (crash), Supercell ID.
