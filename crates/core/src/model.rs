//! Channel-scoped client archive and deterministic navigation ordering.

use gcoms::sdk::{
    ActivityBucket, ChannelId, ChannelRole, ChannelVisibility, PublicChannelDescriptor,
};
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct MemberId(pub [u8; 32]);

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ScopedPmId {
    pub channel_id: ChannelId,
    pub self_member_id: MemberId,
    pub remote_member_id: MemberId,
}

impl Ord for ScopedPmId {
    fn cmp(&self, other: &Self) -> Ordering {
        (
            self.channel_id.0,
            self.self_member_id,
            self.remote_member_id,
        )
            .cmp(&(
                other.channel_id.0,
                other.self_member_id,
                other.remote_member_id,
            ))
    }
}

impl PartialOrd for ScopedPmId {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum HomeId {
    Channel(ChannelId),
    ScopedPm(ScopedPmId),
}

impl Ord for HomeId {
    fn cmp(&self, other: &Self) -> Ordering {
        match (self, other) {
            (Self::Channel(left), Self::Channel(right)) => left.0.cmp(&right.0),
            (Self::Channel(_), Self::ScopedPm(_)) => Ordering::Less,
            (Self::ScopedPm(_), Self::Channel(_)) => Ordering::Greater,
            (Self::ScopedPm(left), Self::ScopedPm(right)) => left.cmp(right),
        }
    }
}

impl PartialOrd for HomeId {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Message {
    pub id: [u8; 16],
    #[serde(skip)]
    pub operation_id: Option<String>,
    #[serde(skip)]
    pub delivery: Option<gchat_api::Delivery>,
    pub ts_unix: u64,
    pub sender_member_id: Option<MemberId>,
    pub sender_name: String,
    pub mine: bool,
    pub text: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MemberRecord {
    pub id: MemberId,
    pub display_name: String,
    pub join_order: u32,
    pub joined_at_unix: Option<u64>,
    pub is_self: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChannelRecord {
    pub id: ChannelId,
    pub protocol_name: String,
    pub title: String,
    pub visibility: ChannelVisibility,
    pub role: ChannelRole,
    pub joined_at_unix: u64,
    pub active: bool,
    pub self_member_id: Option<MemberId>,
    pub members: Vec<MemberRecord>,
    pub messages: Vec<Message>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ScopedPmRecord {
    pub id: ScopedPmId,
    pub remote_display_name: String,
    pub messages: Vec<Message>,
    pub active: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CachedDescriptor {
    pub descriptor: PublicChannelDescriptor,
    pub published_at_unix: u64,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct LegacyArchive {
    pub contacts: crate::contact::ContactBook,
    pub conversations: crate::conversation::Conversations,
}

#[derive(Clone, Debug)]
pub enum HomeItem {
    Joined(ChannelRecord),
    Public(CachedDescriptor),
    ScopedPm(ScopedPmRecord),
}

impl HomeItem {
    pub fn id(&self) -> HomeId {
        match self {
            Self::Joined(channel) => HomeId::Channel(channel.id),
            Self::Public(public) => HomeId::Channel(public.descriptor.channel_id),
            Self::ScopedPm(pm) => HomeId::ScopedPm(pm.id),
        }
    }

    pub fn label(&self) -> String {
        match self {
            Self::Joined(channel) => format!("#{}", channel.title),
            Self::Public(public) => format!("#{} (public)", public.descriptor.title),
            Self::ScopedPm(pm) => {
                format!("@{} in #{}", pm.remote_display_name, pm_channel_title(pm))
            }
        }
    }

    fn messages(&self) -> Option<&[Message]> {
        match self {
            Self::Joined(channel) => Some(&channel.messages),
            Self::ScopedPm(pm) => Some(&pm.messages),
            Self::Public(_) => None,
        }
    }

    fn effective_activity(&self, now: u64) -> u64 {
        if let Some(messages) = self.messages() {
            return messages
                .iter()
                .rev()
                .find(|message| message.mine)
                .or_else(|| messages.last())
                .map_or(0, |message| message.ts_unix);
        }
        match self {
            Self::Public(public) => bucket_floor(public.descriptor.activity, now),
            _ => 0,
        }
    }

    fn joined_or_published(&self) -> u64 {
        match self {
            Self::Joined(channel) => channel.joined_at_unix,
            Self::Public(public) => public.published_at_unix,
            Self::ScopedPm(pm) => pm.messages.first().map_or(0, |message| message.ts_unix),
        }
    }
}

fn pm_channel_title(_pm: &ScopedPmRecord) -> &'static str {
    // App rendering replaces this fallback with the archive channel title.
    "channel"
}

fn bucket_floor(bucket: ActivityBucket, now: u64) -> u64 {
    match bucket {
        ActivityBucket::Today => now.saturating_sub(24 * 60 * 60),
        ActivityBucket::ThisWeek => now.saturating_sub(7 * 24 * 60 * 60),
        ActivityBucket::Older | ActivityBucket::None => 0,
    }
}

pub fn sort_home(items: &mut [HomeItem], now: u64) {
    items.sort_by(|left, right| {
        right
            .effective_activity(now)
            .cmp(&left.effective_activity(now))
            .then_with(|| right.joined_or_published().cmp(&left.joined_or_published()))
            .then_with(|| left.id().cmp(&right.id()))
    });
}

pub fn preserve_selection(items: &[HomeItem], selected: Option<HomeId>) -> usize {
    selected
        .and_then(|id| items.iter().position(|item| item.id() == id))
        .unwrap_or(0)
}

pub fn sort_members(
    members: &mut [MemberRecord],
    pms: &[ScopedPmRecord],
    channel_messages: &[Message],
) {
    members.sort_by(|left, right| {
        let pm_time = |id| {
            pms.iter()
                .find(|pm| pm.id.remote_member_id == id)
                .and_then(|pm| pm.messages.last())
                .map(|message| message.ts_unix)
        };
        let speech_time = |id| {
            channel_messages
                .iter()
                .rev()
                .find(|message| message.sender_member_id == Some(id))
                .map(|message| message.ts_unix)
        };
        compare_optional_desc(pm_time(left.id), pm_time(right.id))
            .then_with(|| compare_optional_desc(speech_time(left.id), speech_time(right.id)))
            .then_with(|| right.joined_at_unix.cmp(&left.joined_at_unix))
            .then_with(|| {
                normalize_name(&left.display_name).cmp(&normalize_name(&right.display_name))
            })
            .then_with(|| left.id.cmp(&right.id))
    });
}

fn compare_optional_desc(left: Option<u64>, right: Option<u64>) -> Ordering {
    right.cmp(&left)
}

fn normalize_name(name: &str) -> String {
    name.trim().to_lowercase()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn id(value: u8) -> ChannelId {
        ChannelId([value; 32])
    }
    fn member(value: u8, name: &str) -> MemberRecord {
        MemberRecord {
            id: MemberId([value; 32]),
            display_name: name.into(),
            join_order: value.into(),
            joined_at_unix: Some(10),
            is_self: false,
        }
    }
    fn message(ts: u64, mine: bool, sender: Option<MemberId>) -> Message {
        Message {
            id: [ts as u8; 16],
            operation_id: None,
            delivery: None,
            ts_unix: ts,
            sender_member_id: sender,
            sender_name: "x".into(),
            mine,
            text: "x".into(),
        }
    }
    fn channel(value: u8, messages: Vec<Message>) -> HomeItem {
        HomeItem::Joined(ChannelRecord {
            id: id(value),
            protocol_name: format!("c{value}"),
            title: "same".into(),
            visibility: ChannelVisibility::Private,
            role: ChannelRole::Member,
            joined_at_unix: 1,
            active: true,
            self_member_id: None,
            members: vec![],
            messages,
        })
    }

    #[test]
    fn home_uses_latest_own_write_then_visible_fallback_and_typed_ties() {
        let mut items = vec![
            channel(2, vec![message(20, false, None)]),
            channel(1, vec![message(10, true, None), message(99, false, None)]),
            channel(3, vec![message(30, true, None)]),
        ];
        sort_home(&mut items, 100);
        assert_eq!(
            items.iter().map(HomeItem::id).collect::<Vec<_>>(),
            vec![
                HomeId::Channel(id(3)),
                HomeId::Channel(id(2)),
                HomeId::Channel(id(1))
            ]
        );
        let selected = Some(HomeId::Channel(id(2)));
        items.swap(0, 1);
        assert_eq!(preserve_selection(&items, selected), 0);
    }

    #[test]
    fn public_bucket_is_conservative_and_names_do_not_form_keys() {
        let descriptor = |value, activity| CachedDescriptor {
            descriptor: PublicChannelDescriptor {
                version: 1,
                expires_at_unix: 999,
                channel_id: id(value),
                owner_public_key: vec![],
                capacity: 2,
                title: "same".into(),
                description: String::new(),
                activity,
                automatic_join: gcoms::sdk::AutomaticJoinEndpoint {
                    catalog: String::new(),
                    endpoint: String::new(),
                },
                signature: vec![],
            },
            published_at_unix: 1,
        };
        let mut items = vec![
            HomeItem::Public(descriptor(2, ActivityBucket::ThisWeek)),
            HomeItem::Public(descriptor(1, ActivityBucket::Today)),
        ];
        sort_home(&mut items, 100);
        assert_eq!(items[0].id(), HomeId::Channel(id(1)));
    }

    #[test]
    fn member_pm_precedes_speech_then_inactive_ties_are_stable() {
        let self_id = MemberId([9; 32]);
        let mut members = vec![member(3, "same"), member(2, "Same"), member(1, "z")];
        let pms = vec![ScopedPmRecord {
            id: ScopedPmId {
                channel_id: id(1),
                self_member_id: self_id,
                remote_member_id: MemberId([2; 32]),
            },
            remote_display_name: "Same".into(),
            messages: vec![message(5, false, None)],
            active: true,
        }];
        let speech = vec![message(100, false, Some(MemberId([1; 32])))];
        sort_members(&mut members, &pms, &speech);
        assert_eq!(
            members.iter().map(|m| m.id).collect::<Vec<_>>(),
            vec![MemberId([2; 32]), MemberId([1; 32]), MemberId([3; 32])]
        );
    }
}
