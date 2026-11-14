-- Django's preserved model table names are presented as updatable views.
-- Each view writes through to its Supabase-owned application table.
create or replace view public.ablog_bloger with (security_invoker = true) as select id, sender_id, image_path as image, description, service_id, created_at as created from public.blog_posts;
create or replace view public.afollows_connection with (security_invoker = true) as select id, sender_id, receiver_id, accepted, updated_at as updated, created_at as created from public.connections;
create or replace view public.amessages_message with (security_invoker = true) as select id, connection_id, sender_id, image_path as image, red, description, created_at as created from public.direct_messages;
create or replace view public.amessages_tagedmessage with (security_invoker = true) as select id, message_id, connection_id, created_at as created from public.tagged_messages;
create or replace view public.amonetization_pagevisit with (security_invoker = true) as select id, user_id, page_name, session_id, ip_address, user_agent, visited_at from public.page_visits;
create or replace view public.amonetization_monetizationanalytics with (security_invoker = true) as select id, date, page_name, total_visits, unique_visitors, engagement_rate, link_clicks, profile_visits, likes, replies, reposts, new_followers, previous_period_visits, visit_change_percentage, created_at, updated_at from public.monetization_analytics;
create or replace view public.amonetization_marketing with (security_invoker = true) as select id, owner_id, title, description, media, price, currency, category, tags, external_link, contact_email, contact_phone, views, active, metadata, created_at, updated_at from public.marketing_items;
create or replace view public.amonetization_librarymarketing with (security_invoker = true) as select id, owner_id, title, description, files, tags, access_level, downloads, active, metadata, created_at, updated_at from public.library_marketing_items;
create or replace view public.amonetization_campusmap with (security_invoker = true) as select id, name, description, geo_lat, geo_lng, building, floor, floor_plan_url, opening_hours, accessibility, contact, active, created_at, updated_at from public.campus_maps;
create or replace view public.amonetization_onlinetransaction with (security_invoker = true) as select id, provider_id, provider_location, geo_lat, geo_lng, method, description, active, metadata, created_at, updated_at from public.online_transactions;
create or replace view public.amonetization_accommodation with (security_invoker = true) as select id, sender_id, title, description, price, currency, images, geo_lat, geo_lng, location, phone, inquiries, virtual_views, verify_badge, created_at, updated_at from public.accommodations;
create or replace view public.amonetization_lostitem with (security_invoker = true) as select id, reporter_id, title, description, category, location, date_lost, images, reward_offered, currency, contact_info, status, is_premium, views, reported_by_id, metadata, created_at, updated_at from public.lost_items;
create or replace view public.amonetization_founditem with (security_invoker = true) as select id, reporter_id, title, description, category, location, date_found, images, contact_info, status, is_premium, views, reported_by_id, metadata, created_at, updated_at from public.found_items;
create or replace view public.amonetization_lostfoundmatch with (security_invoker = true) as select id, lost_item_id, found_item_id, match_confidence, matched_by_id, status, notes, created_at, updated_at from public.lost_found_matches;
create or replace view public.amonetization_lostfoundreward with (security_invoker = true) as select id, lost_item_id, found_item_id, reporter_reward, finder_reward, currency, status, transaction_id, metadata, created_at, updated_at from public.lost_found_rewards;
create or replace view public.amonetization_serviceguide with (security_invoker = true) as select id, service_name, service_type, department, description, contact_person, contact_email, contact_phone, location, operating_hours, website_url, is_verified, is_active, views, search_keywords, metadata, created_at, updated_at from public.service_guides;
create or replace view public.amonetization_servicedocument with (security_invoker = true) as select id, service_guide_id, title, description, document_file_path as document_file, file_size, is_processed, extracted_text, processing_status, version, is_current, uploaded_by_id, uploaded_via_email, email_message_id, metadata, created_at, updated_at from public.service_documents;
create or replace view public.amonetization_serviceguidesearch with (security_invoker = true) as select id, query, response, confidence_score, user_id, search_metadata, created_at from public.service_guide_searches;
create or replace view public.amonetization_serviceguideanalytics with (security_invoker = true) as select id, service_guide_id, date, views, searches, document_downloads, unique_visitors, avg_confidence_score, created_at, updated_at from public.service_guide_analytics;
create or replace view public.anotif_notif with (security_invoker = true) as select id, sender_id, service_id, update_type, description, image_path as image, extra_data, created_at as created from public.service_notifications;
create or replace view public.anotif_comment with (security_invoker = true) as select id, notification_id as post_id, sender_id, description, created_at as created from public.service_notification_comments;
create or replace view public.anotif_comments with (security_invoker = true) as select id, notification_id as post_id, sender_id, description, created_at as created from public.service_notification_comments;
create or replace view public.anotif_poll with (security_invoker = true) as select notification_id, update_type, title, poll_question, poll_type, category, visibility, poll_sections, images, settings, duration_hours, expires_at, total_votes, total_voters, unique_voter_count, is_active, expired, allow_comments, allow_multiple_votes, anonymous_voting, hide_results_until_expired, show_results_after_vote, send_reminders, reminder_frequency_hours, tags, created_at, updated_at from public.polls;
create or replace view public.app_notif_appnotif with (security_invoker = true) as select id, service_id as sender_id, sender_user_id, image_path as image, subject, description, created_at as created from public.app_notifications;
create or replace view public.app_notif_appfeedback with (security_invoker = true) as select id, sender_id, image_path as image, description, created_at as created from public.app_feedback;
create or replace view public.app_notif_appreport with (security_invoker = true) as select id, sender_id, image_path as image, subject, description, created_at as created from public.app_reports;
create or replace view public.asearch_searchtrend with (security_invoker = true) as select id, query, created_at from public.search_trends;
create or replace view public.ausernotif_notif_user_post_liked with (security_invoker = true) as select id, interactor_id, notif_type, description, post_id, red, created_at as created from public.user_post_notifications;
create or replace view public.ausernotif_notif_user_post_commented with (security_invoker = true) as select id, interactor_id, notif_type, description, post_id, red, created_at as created from public.user_post_comment_notifications;
create or replace view public.ausernotif_notif_user with (security_invoker = true) as select id, recipient_id, sender_id, notif_type, description, related_id, is_read, content_type, extra_data, created_at as created from public.user_notifications;
create or replace view public.auserpost_post with (security_invoker = true) as select id, sender_id, image_path as image, description, created_at as created from public.user_posts;
create or replace view public.auserpost_comment with (security_invoker = true) as select id, post_id, sender_id, description, created_at as created from public.user_post_comments;
create or replace view public.community_groupcon with (security_invoker = true) as select id, name, creator_id, updated_at as updated, created_at as created from public.group_connections;
create or replace view public.community_groupchat with (security_invoker = true) as select id, connection_id, sender_id, text, created_at as created from public.group_messages;
create or replace view public.quercus_quercusconversation with (security_invoker = true) as select id, user_id, conversation_id, title, created_at, updated_at, is_active from public.quercus_conversations;
create or replace view public.quercus_quercusmessage with (security_invoker = true) as select id, conversation_id, message_id, content, is_user, timestamp, metadata, model_used, tokens_used, response_time_ms, prompt_tokens, completion_tokens, total_tokens, generation_config, safety_ratings, finish_reason from public.quercus_messages;
create or replace view public.quercus_quercussettings with (security_invoker = true) as select user_id, response_style, auto_save, notifications_enabled, study_reminders, campus_updates, created_at, updated_at from public.quercus_settings;
create or replace view public.quercus_quercusprompt with (security_invoker = true) as select id, user_id, title, prompt, category, is_active, usage_count, created_at from public.quercus_prompts;
create or replace view public.quercus_quercusanalytics with (security_invoker = true) as select id, user_id, date, total_queries, study_queries, schedule_queries, campus_queries, career_queries, avg_response_time, satisfaction_rating from public.quercus_analytics;
create or replace view public.quercus_quercuscampusresource with (security_invoker = true) as select id, name, description, resource_type, location, building, room_number, operating_hours, contact_info, tags, is_active, created_at, updated_at from public.quercus_campus_resources;
create or replace view public.quercus_quercusstudyplan with (security_invoker = true) as select id, user_id, subject, duration_weeks, difficulty_level, plan_data, is_completed, progress_percentage, created_at, updated_at from public.quercus_study_plans;
create or replace view public.quercus_quercuscareerguidance with (security_invoker = true) as select id, user_id, field_of_study, interests, guidance_data, follow_up_questions, is_bookmarked, created_at, updated_at from public.quercus_career_guidance;
create or replace view public.ablog_bloger_tags with (security_invoker = true) as select blog_post_id as bloger_id, user_id from public.blog_post_tags;
create or replace view public.ablog_bloger_interactions with (security_invoker = true) as select blog_post_id as bloger_id, user_id from public.blog_post_interactions;
create or replace view public.ablog_bloger_shared with (security_invoker = true) as select blog_post_id as bloger_id, user_id from public.blog_post_shares;
create or replace view public.api_communitydirectory_followers with (security_invoker = true) as select directory_id as communitydirectory_id, user_id from public.community_directory_followers;
create or replace view public.api_communitydirectory_moderators with (security_invoker = true) as select directory_id as communitydirectory_id, user_id from public.community_directory_moderators;
create or replace view public.anotif_notif_likes with (security_invoker = true) as select notification_id as notif_id, user_id from public.service_notification_likes;
create or replace view public.anotif_notif_interactions with (security_invoker = true) as select notification_id as notif_id, user_id from public.service_notification_interactions;
create or replace view public.anotif_comment_interactions with (security_invoker = true) as select comment_id, user_id from public.service_notification_comment_interactions;
create or replace view public.anotif_comment_likes with (security_invoker = true) as select comment_id, user_id from public.service_notification_comment_likes;
create or replace view public.app_notif_appnotif_receiver with (security_invoker = true) as select notification_id as appnotif_id, user_id from public.app_notification_recipients;
create or replace view public.app_notif_appnotif_interactions with (security_invoker = true) as select notification_id as appnotif_id, user_id from public.app_notification_interactions;
create or replace view public.app_notif_appfeedback_attendand with (security_invoker = true) as select feedback_id as appfeedback_id, user_id from public.app_feedback_attendees;
create or replace view public.app_notif_appfeedback_red_by with (security_invoker = true) as select feedback_id as appfeedback_id, user_id from public.app_feedback_read_by;
create or replace view public.app_notif_appreport_attendand with (security_invoker = true) as select report_id as appreport_id, user_id from public.app_report_attendees;
create or replace view public.app_notif_appreport_red_by with (security_invoker = true) as select report_id as appreport_id, user_id from public.app_report_read_by;
create or replace view public.auserpost_post_interactions with (security_invoker = true) as select post_id, user_id from public.user_post_interactions;
create or replace view public.auserpost_post_likes with (security_invoker = true) as select post_id, user_id from public.user_post_likes;
create or replace view public.auserpost_comment_interactions with (security_invoker = true) as select comment_id, user_id from public.user_post_comment_interactions;
create or replace view public.auserpost_comment_likes with (security_invoker = true) as select comment_id, user_id from public.user_post_comment_likes;
create or replace view public.community_groupcon_users with (security_invoker = true) as select group_id as groupcon_id, user_id from public.group_members;
create or replace view public.amonetization_serviceguidesearch_relevant_documents with (security_invoker = true) as select search_id as serviceguidesearch_id, document_id as servicedocument_id from public.service_guide_search_documents;

create or replace function public.set_directory_moderator_assigner()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if new.assigned_by is null then
    select creator_id into new.assigned_by
    from public.community_directories
    where id = new.directory_id;
  end if;
  return new;
end;
$$;

drop trigger if exists set_directory_moderator_assigner on public.community_directory_moderators;
create trigger set_directory_moderator_assigner
before insert on public.community_directory_moderators
for each row execute function public.set_directory_moderator_assigner();
