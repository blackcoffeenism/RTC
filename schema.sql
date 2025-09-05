-- Supabase SQL Schema for Hotel/Restaurant Management App

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for Rooms
CREATE TABLE rooms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    number TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('VIP', 'Regular')),
    status TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'occupied')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for Photo Menu Items
CREATE TABLE menu_photo (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    photo_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for List Menu Items
CREATE TABLE menu_list (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for Events
CREATE TABLE events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    venue TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_menu_photo_name ON menu_photo(name);
CREATE INDEX idx_menu_list_title ON menu_list(title);
CREATE INDEX idx_events_date ON events(date);

-- Enable Row Level Security (RLS) for all tables
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_photo ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Create policies for user-specific access
-- For rooms
CREATE POLICY "Users can access their own rooms" ON rooms FOR ALL USING (auth.uid() = user_id);

-- For menu_photo
CREATE POLICY "Users can access their own menu_photo" ON menu_photo FOR ALL USING (auth.uid() = user_id);

-- For menu_list
CREATE POLICY "Users can access their own menu_list" ON menu_list FOR ALL USING (auth.uid() = user_id);

-- For events
CREATE POLICY "Users can access their own events" ON events FOR ALL USING (auth.uid() = user_id);
