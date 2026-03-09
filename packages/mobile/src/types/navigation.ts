import type { NavigatorScreenParams, RouteProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp } from '@react-navigation/native';

export type HomeStackParamList = {
  HomeRoot: undefined;
  SeedGenerator: undefined;
  Validation: undefined;
  Lineage: undefined;
  Blueprints: undefined;
  BlueprintEditor: { path: string };
  BatchGenerate: undefined;
};

export type DraftsStackParamList = {
  DraftsList: undefined;
  DraftDetail: { draftId: string };
  Chat: { draftId: string; asset?: string };
};

export type RootTabParamList = {
  Home: NavigatorScreenParams<HomeStackParamList> | undefined;
  Generate: { seed?: string } | undefined;
  Drafts: NavigatorScreenParams<DraftsStackParamList> | undefined;
  Templates: undefined;
  Compare: { character1?: string; character2?: string } | undefined;
  Offspring: { parent1?: string; parent2?: string } | undefined;
  Settings: undefined;
};

export type HomeScreenNavigationProp = CompositeNavigationProp<
  NativeStackNavigationProp<HomeStackParamList, 'HomeRoot'>,
  BottomTabNavigationProp<RootTabParamList>
>;

export type HomeStackNavigationProp<RouteName extends keyof HomeStackParamList> = CompositeNavigationProp<
  NativeStackNavigationProp<HomeStackParamList, RouteName>,
  BottomTabNavigationProp<RootTabParamList>
>;

export type DraftsStackNavigationProp<RouteName extends keyof DraftsStackParamList> =
  NativeStackNavigationProp<DraftsStackParamList, RouteName>;

export type RootTabNavigationProp<RouteName extends keyof RootTabParamList> =
  BottomTabNavigationProp<RootTabParamList, RouteName>;

export type GenerateRouteProp = RouteProp<RootTabParamList, 'Generate'>;
export type CompareRouteProp = RouteProp<RootTabParamList, 'Compare'>;
export type OffspringRouteProp = RouteProp<RootTabParamList, 'Offspring'>;
export type DraftDetailRouteProp = RouteProp<DraftsStackParamList, 'DraftDetail'>;
export type ChatRouteProp = RouteProp<DraftsStackParamList, 'Chat'>;
export type BlueprintEditorRouteProp = RouteProp<HomeStackParamList, 'BlueprintEditor'>;