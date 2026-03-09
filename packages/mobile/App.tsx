import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { DraftsStackParamList, HomeStackParamList, RootTabParamList } from './src/types/navigation';
import { HomeIcon, SparklesIcon, FolderIcon, Cog6ToothIcon, DocumentTextIcon, GitCompareIcon, BabyIcon } from './src/components/Icons';

import HomeScreen from './src/screens/HomeScreen';
import GenerateScreen from './src/screens/GenerateScreen';
import DraftsScreen from './src/screens/DraftsScreen';
import DraftDetailScreen from './src/screens/DraftDetailScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import TemplatesScreen from './src/screens/TemplatesScreen';
import SimilarityScreen from './src/screens/SimilarityScreen';
import OffspringScreen from './src/screens/OffspringScreen';
import ChatScreen from './src/screens/ChatScreen';
import SeedGeneratorScreen from './src/screens/SeedGeneratorScreen';
import ValidationScreen from './src/screens/ValidationScreen';
import LineageScreen from './src/screens/LineageScreen';
import BlueprintsScreen from './src/screens/BlueprintsScreen';
import BatchGenerateScreen from './src/screens/BatchGenerateScreen';
import BlueprintEditorScreen from './src/screens/BlueprintEditorScreen';

const Tab = createBottomTabNavigator<RootTabParamList>();
const HomeStackNavigator = createNativeStackNavigator<HomeStackParamList>();
const DraftsStackNavigator = createNativeStackNavigator<DraftsStackParamList>();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

function HomeStack() {
  return (
    <HomeStackNavigator.Navigator>
      <HomeStackNavigator.Screen name="HomeRoot" component={HomeScreen} options={{ title: 'Home' }} />
      <HomeStackNavigator.Screen name="SeedGenerator" component={SeedGeneratorScreen} options={{ title: 'Seed Generator' }} />
      <HomeStackNavigator.Screen name="Validation" component={ValidationScreen} options={{ title: 'Validation' }} />
      <HomeStackNavigator.Screen name="Lineage" component={LineageScreen} options={{ title: 'Lineage' }} />
      <HomeStackNavigator.Screen name="Blueprints" component={BlueprintsScreen} options={{ title: 'Blueprints' }} />
      <HomeStackNavigator.Screen name="BlueprintEditor" component={BlueprintEditorScreen} options={{ title: 'Edit Blueprint' }} />
      <HomeStackNavigator.Screen name="BatchGenerate" component={BatchGenerateScreen} options={{ title: 'Batch Generation' }} />
    </HomeStackNavigator.Navigator>
  );
}

function DraftsStack() {
  return (
    <DraftsStackNavigator.Navigator>
      <DraftsStackNavigator.Screen name="DraftsList" component={DraftsScreen} options={{ title: 'Drafts' }} />
      <DraftsStackNavigator.Screen name="DraftDetail" component={DraftDetailScreen} options={{ title: 'Character' }} />
      <DraftsStackNavigator.Screen name="Chat" component={ChatScreen} options={{ title: 'Refine Character' }} />
    </DraftsStackNavigator.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#7c3aed',
        tabBarInactiveTintColor: '#6b7280',
        headerStyle: { backgroundColor: '#18181b' },
        headerTintColor: '#fff',
        tabBarStyle: { backgroundColor: '#18181b' },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeStack}
        options={{
          tabBarIcon: ({ color }) => <HomeIcon color={color} />,
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Generate"
        component={GenerateScreen}
        options={{
          tabBarIcon: ({ color }) => <SparklesIcon color={color} />,
        }}
      />
      <Tab.Screen
        name="Drafts"
        component={DraftsStack}
        options={{
          tabBarIcon: ({ color }) => <FolderIcon color={color} />,
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Templates"
        component={TemplatesScreen}
        options={{
          tabBarIcon: ({ color }) => <DocumentTextIcon color={color} />,
        }}
      />
      <Tab.Screen
        name="Compare"
        component={SimilarityScreen}
        options={{
          tabBarIcon: ({ color }) => <GitCompareIcon color={color} />,
        }}
      />
      <Tab.Screen
        name="Offspring"
        component={OffspringScreen}
        options={{
          tabBarIcon: ({ color }) => <BabyIcon color={color} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ color }) => <Cog6ToothIcon color={color} />,
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <NavigationContainer>
          <StatusBar style="light" />
          <MainTabs />
        </NavigationContainer>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
