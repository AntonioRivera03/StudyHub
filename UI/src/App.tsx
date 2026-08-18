import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { FocusPage } from './pages/FocusPage';
import { DeckPage } from './pages/DeckPage';
import { FlashcardsPage } from './pages/FlashcardsPage';
import { ReviewPage } from './pages/ReviewPage';
import { TodayPage } from './pages/TodayPage';

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<TodayPage />} />
        <Route path="focus" element={<FocusPage />} />
        <Route path="flashcards" element={<FlashcardsPage />} />
        <Route path="flashcards/decks/:deckId" element={<DeckPage />} />
        <Route path="flashcards/review/:reviewId" element={<ReviewPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
