use std::convert::TryFrom;
use teloxide::prelude::*;
use ruma_identifiers::RoomId;
use ruma_client::Client;
// use ruma::{
//     api::client::r0::{alias::get_alias, membership::join_room_by_id, message::send_message_event},
//     events::{room::message::MessageEventContent, AnyMessageEventContent},
//     RoomAliasId,
// };
use ruma_client_api::r0::message::create_message_event::Request;
use ruma_events::AnyMessageEventContent;

#[tokio::main]
async fn main() {
    // use ruma_client::Client;
    let homeserver_url = "https://matrix.org".parse().unwrap();
    let client = Client::https(homeserver_url, None);
    
    let session = client.log_in("@someone.matrix.org".to_string(), "access_token".to_string(), None, None).await;
    let room_id = RoomId::try_from("!JULKXysoyAyDsswIkV:matrix.org").unwrap();
    Request::new(room_id, "1", );
    // client.request(create_message_event::Request::new(
    //     &room_id,
    //     "1",
        
    // ))
    
    teloxide::enable_logging!();
    log::info!("Starting dices_bot...");

    let bot = Bot::from_env();
    let result = bot.send_message(teloxide::types::ChatId::Id(123456789), "Hello World!").send().await;
    result.log_on_error().await;
    // match result {
    //     Ok(v) => log::info!("Ok"),
    //     Err(e) => log::error!("Failed"),
    // }

    teloxide::repl(bot, |message| async move {
        log::info!("Message from {}", message.chat_id());
        // message.answer_str("Yes!")//.send().await?;
        ResponseResult::<()>::Ok(())
    })
    .await;
}

// MDAxOGxvY2F0aW9uIG1hdHJpeC5vcmcKMDAxM2lkZW50aWZpZXIga2V5CjAwMTBjaWQgZ2VuID0gMQowMDI1Y2lkIHVzZXJfaWQgPSBAaDNuZHJrOm1hdHJpeC5vcmcKMDAxNmNpZCB0eXBlID0gYWNjZXNzCjAwMjFjaWQgbm9uY2UgPSBeVHhpRENTIyYxU0xrVUwsCjAwMmZzaWduYXR1cmUg3UBFHo5mBbT3f7vaKsLvKn389ukhzIX73O6ZvmUV28kK
